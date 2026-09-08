"""Excel export and guarded import helpers for Inventory Search Report."""

from __future__ import annotations

import hashlib
import io
import json
import uuid
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation

import frappe
from frappe.utils import escape_html, flt


SUMMARY_SHEET = "SKU Summary"
DETAIL_SHEET = "Breakup Details"
INSTRUCTIONS_SHEET = "Instructions"

SUMMARY_HEADERS = [
    "SKU Code",
    "Item",
    "Warehouse",
    "Metal",
    "Supplier",
    "Weight",
    "Qty",
    "Cost Price",
    "Selling Price",
    "Status",
    "SKU Master",
    "Breakup Ref",
    "Update Breakup Details",
    "Breakup Summary",
]

DETAIL_HEADERS = [
    "SKU Code",
    "SKU Master",
    "Breakup Ref",
    "Row No.",
    "Attribute Type",
    "Attribute Value",
    "Weight",
    "Price",
    "Unit",
]

EDITABLE_SUMMARY_HEADERS = {
    "Metal",
    "Supplier",
    "Cost Price",
    "Selling Price",
    "Update Breakup Details",
}
EDITABLE_DETAIL_HEADERS = {
    "Attribute Type",
    "Attribute Value",
    "Weight",
    "Price",
    "Unit",
}
MAX_IMPORT_BYTES = 10 * 1024 * 1024
CACHE_PREFIX = "inventory_search_report_sku_breakup_import"


def download_workbook(filters=None, template_only=False):
    """Build and return a Frappe download response for an export or template."""
    filters = _parse_filters(filters)
    workbook_bytes = build_workbook(filters=filters, template_only=template_only)

    frappe.response["filename"] = (
        "sku_breakup_import_template.xlsx" if template_only else "inventory_search_report_sku_breakup.xlsx"
    )
    frappe.response["filecontent"] = workbook_bytes
    frappe.response["type"] = "download"


def build_workbook(filters=None, template_only=False):
    """Create the three-sheet workbook as bytes.

    This deliberately reads the same report rows used on screen so warehouse and
    quantity aggregation exactly reflects the selected report filters.
    """
    Workbook, _, Alignment, Font, PatternFill = _openpyxl()
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = SUMMARY_SHEET
    detail_sheet = workbook.create_sheet(DETAIL_SHEET)
    instruction_sheet = workbook.create_sheet(INSTRUCTIONS_SHEET)

    summary_rows = []
    detail_rows = []
    if not template_only:
        summary_rows, detail_rows = _get_export_rows(filters or {})

    _write_table(
        summary_sheet,
        SUMMARY_HEADERS,
        summary_rows,
        EDITABLE_SUMMARY_HEADERS,
        Alignment,
        Font,
        PatternFill,
    )
    _write_table(
        detail_sheet,
        DETAIL_HEADERS,
        detail_rows,
        EDITABLE_DETAIL_HEADERS,
        Alignment,
        Font,
        PatternFill,
    )
    _write_instructions(instruction_sheet, Alignment, Font, PatternFill)

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def validate_import_file(file_url):
    """Validate the uploaded workbook and cache a short-lived confirmation token."""
    content, file_doc = _get_upload_content(file_url)
    result = validate_import_content(content)
    if result["errors"]:
        return {"ok": False, "errors": result["errors"]}

    token = uuid.uuid4().hex
    cache_key = _cache_key(token)
    frappe.cache.set_value(
        cache_key,
        {
            "file_url": file_doc.file_url,
            "content_hash": hashlib.sha256(content).hexdigest(),
        },
        expires_in_sec=15 * 60,
    )
    return {
        "ok": True,
        "import_token": token,
        "sku_count": len(result["prepared"]),
        "breakup_update_count": sum(row["replace_breakups"] for row in result["prepared"]),
    }


def apply_import(import_token):
    """Revalidate and import the exact file approved by the user.

    No explicit commit occurs here. Frappe commits at the successful end of this
    request and rolls the whole request back if a save or breakup validation fails.
    """
    cached = frappe.cache.get_value(_cache_key(import_token))
    if not cached:
        frappe.throw("The import confirmation has expired. Please upload and validate the file again.")

    content, _ = _get_upload_content(cached["file_url"])
    if hashlib.sha256(content).hexdigest() != cached["content_hash"]:
        frappe.throw("The uploaded file changed after validation. Please validate it again.")

    result = validate_import_content(content)
    if result["errors"]:
        frappe.throw(_format_errors(result["errors"]), title="Import validation failed")

    from arnav_customization.arnav_customization.doctype.sku_master.sku_master import save_breakup_rows

    updated_skus = 0
    updated_breakups = 0
    for item in result["prepared"]:
        sku_doc = frappe.get_doc("SKU", item["sku_name"])
        sku_doc.check_permission("write")

        if item["sku_updates"]:
            for fieldname, value in item["sku_updates"].items():
                sku_doc.set(fieldname, value)
            sku_doc.save()
            updated_skus += 1

        if not item["replace_breakups"]:
            continue

        # This existing function owns deletion/insertion and its Design Code / locked
        # classification safeguards. Do not replace it with direct SKU Breakup writes.
        saved = save_breakup_rows(
            item["sku_master"],
            item["breakup_ref"],
            json.dumps(item["breakup_rows"]),
        )
        _synchronise_breakup_reference(item, saved["breakup_ref"])
        updated_breakups += 1

    frappe.cache.delete_value(_cache_key(import_token))
    return {
        "ok": True,
        "updated_skus": updated_skus,
        "updated_breakups": updated_breakups,
    }


def validate_import_content(content):
    """Parse and validate every requested change without writing to the database."""
    errors = []
    try:
        workbook = _load_import_workbook(content)
    except Exception as error:
        return {"errors": [f"Unable to read the workbook: {error}"], "prepared": []}

    sheets = {sheet.title: sheet for sheet in workbook.worksheets}
    for sheet_name in (SUMMARY_SHEET, DETAIL_SHEET, INSTRUCTIONS_SHEET):
        if sheet_name not in sheets:
            errors.append(f"Missing required sheet: {sheet_name}.")

    if errors:
        return {"errors": errors, "prepared": []}

    summary_rows = _read_sheet(sheets[SUMMARY_SHEET], SUMMARY_HEADERS, errors)
    detail_rows = _read_sheet(sheets[DETAIL_SHEET], DETAIL_HEADERS, errors)
    if errors:
        return {"errors": errors, "prepared": []}

    prepared = _validate_rows(summary_rows, detail_rows, errors)
    return {"errors": errors, "prepared": prepared}


def _get_export_rows(filters):
    # Importing here avoids a module cycle while retaining the report's exact data logic.
    from .inventory_search_report import get_data
    from arnav_customization.arnav_customization.doctype.sku_master.sku_master import (
        get_breakup_rows_for_reference,
    )

    grouped = OrderedDict()
    for report_row in get_data(filters):
        sku_code = report_row.get("sku_code")
        if not sku_code:
            continue
        item = grouped.setdefault(
            sku_code,
            {
                "row": report_row,
                "warehouses": [],
                "qty": 0,
            },
        )
        warehouse = report_row.get("warehouse")
        if warehouse and warehouse not in item["warehouses"]:
            item["warehouses"].append(warehouse)
        item["qty"] += flt(report_row.get("qty"))

    summary_rows = []
    detail_rows = []
    for sku_code, item in grouped.items():
        report_row = item["row"]
        sku_master = report_row.get("sku_master")
        breakup_ref = report_row.get("breakup_ref")
        breakup_rows = get_breakup_rows_for_reference(sku_master, breakup_ref) if sku_master else []

        summary_rows.append(
            [
                sku_code,
                report_row.get("product"),
                ", ".join(item["warehouses"]),
                report_row.get("metal"),
                report_row.get("supplier"),
                report_row.get("weight"),
                item["qty"],
                report_row.get("cost_price"),
                report_row.get("selling_price"),
                report_row.get("status"),
                sku_master,
                breakup_ref,
                "No",
                _breakup_summary(breakup_rows),
            ]
        )

        for row_number, breakup_row in enumerate(breakup_rows, start=1):
            detail_rows.append(
                [
                    sku_code,
                    sku_master,
                    breakup_ref,
                    row_number,
                    breakup_row.get("attribute_type"),
                    breakup_row.get("attribute_value"),
                    breakup_row.get("weight"),
                    breakup_row.get("price"),
                    breakup_row.get("unit"),
                ]
            )

    return summary_rows, detail_rows


def _validate_rows(summary_rows, detail_rows, errors):
    if not summary_rows:
        errors.append(f"{SUMMARY_SHEET} has no SKU rows.")
        return []

    sku_meta = frappe.get_meta("SKU")
    breakup_meta = frappe.get_meta("SKU Breakup")
    attribute_type_options = _select_options(breakup_meta.get_field("attribute_type"))
    unit_options = _select_options(breakup_meta.get_field("unit"))
    sku_by_code = {}
    prepared = []

    for sheet_row, row in summary_rows:
        prefix = f"{SUMMARY_SHEET} row {sheet_row}"
        sku_code = _text(row["SKU Code"])
        if not sku_code:
            errors.append(f"{prefix}: SKU Code is required.")
            continue
        if sku_code in sku_by_code:
            errors.append(f"{prefix}: SKU Code '{sku_code}' appears more than once.")
            continue

        sku = _get_sku_for_code(sku_code, prefix, errors)
        if not sku:
            continue
        sku_by_code[sku_code] = sku

        _validate_reference_value(
            row["SKU Master"], sku.get("sku_master"), "SKU Master", prefix, errors
        )
        _validate_reference_value(
            row["Breakup Ref"], sku.get("breakup_ref"), "Breakup Ref", prefix, errors
        )

        updates = {}
        for header, fieldname in (
            ("Metal", "metal"),
            ("Supplier", "supplier"),
        ):
            value = _text(row[header])
            if value:
                if _validate_sku_link(sku_meta, fieldname, value, prefix, errors):
                    updates[fieldname] = value

        for header, fieldname in (("Cost Price", "cost_price"), ("Selling Price", "selling_price")):
            value = _number(row[header], f"{prefix}: {header}", errors)
            if value is not None and _validate_sku_numeric_field(sku_meta, fieldname, prefix, errors):
                updates[fieldname] = value

        replace_breakups = _yes_no(row["Update Breakup Details"], prefix, errors)
        prepared.append(
            {
                "sku_name": sku.name,
                "sku_code": sku_code,
                "sku_master": sku.get("sku_master"),
                "breakup_ref": sku.get("breakup_ref"),
                "sku_updates": updates,
                "replace_breakups": replace_breakups,
                "breakup_rows": [],
            }
        )

    prepared_by_code = {item["sku_code"]: item for item in prepared}
    breakup_row_numbers = defaultdict(set)
    breakup_order = defaultdict(int)
    for sheet_row, row in detail_rows:
        prefix = f"{DETAIL_SHEET} row {sheet_row}"
        sku_code = _text(row["SKU Code"])
        if not sku_code:
            errors.append(f"{prefix}: SKU Code is required.")
            continue
        item = prepared_by_code.get(sku_code)
        if not item:
            errors.append(f"{prefix}: SKU Code '{sku_code}' is not present in {SUMMARY_SHEET}.")
            continue

        _validate_reference_value(
            row["SKU Master"], item["sku_master"], "SKU Master", prefix, errors
        )
        _validate_reference_value(
            row["Breakup Ref"], item["breakup_ref"], "Breakup Ref", prefix, errors
        )
        if not item["replace_breakups"]:
            errors.append(
                f"{prefix}: set Update Breakup Details to Yes for SKU Code '{sku_code}' before importing breakup rows."
            )

        row_number = _row_number(row["Row No."], prefix, errors)
        if row_number is not None:
            if row_number in breakup_row_numbers[sku_code]:
                errors.append(f"{prefix}: Row No. {row_number} is duplicated for SKU Code '{sku_code}'.")
            breakup_row_numbers[sku_code].add(row_number)
        breakup_order[sku_code] += 1

        attribute_type = _text(row["Attribute Type"])
        attribute_value = _text(row["Attribute Value"])
        if not attribute_type:
            errors.append(f"{prefix}: Attribute Type is required.")
        elif attribute_type not in attribute_type_options:
            allowed = ", ".join(attribute_type_options)
            errors.append(f"{prefix}: Attribute Type '{attribute_type}' is invalid. Allowed values: {allowed}.")

        if not attribute_value:
            errors.append(f"{prefix}: Attribute Value is required.")
        elif attribute_type in attribute_type_options:
            _validate_link_value(attribute_type, attribute_value, "Attribute Value", prefix, errors)

        unit = _text(row["Unit"])
        if unit and unit not in unit_options:
            allowed = ", ".join(unit_options)
            errors.append(f"{prefix}: Unit '{unit}' is invalid. Allowed values: {allowed}.")

        breakup_row = {
            "attribute_type": attribute_type,
            "attribute_value": attribute_value,
            "weight": _number(row["Weight"], f"{prefix}: Weight", errors),
            "price": _number(row["Price"], f"{prefix}: Price", errors),
            "unit": unit,
            "_row_number": row_number if row_number is not None else breakup_order[sku_code],
        }
        item["breakup_rows"].append(breakup_row)

    for item in prepared:
        if item["replace_breakups"] and not item["sku_master"]:
            errors.append(
                f"SKU Code '{item['sku_code']}': SKU Master is required before breakup details can be updated."
            )
        if item["replace_breakups"]:
            if item["sku_master"] and not frappe.has_permission(
                "SKU Master", "write", item["sku_master"]
            ):
                errors.append(
                    f"SKU Code '{item['sku_code']}': you do not have permission to update SKU Master "
                    f"'{item['sku_master']}'."
                )
            _validate_linked_sku_detail_is_unambiguous(item, errors)
        item["breakup_rows"].sort(key=lambda breakup_row: breakup_row.pop("_row_number"))

    return prepared


def _get_sku_for_code(sku_code, prefix, errors):
    records = frappe.get_all(
        "SKU",
        filters={"sku_code": sku_code},
        fields=["name", "sku_code", "sku_master", "breakup_ref"],
        limit_page_length=2,
    )
    if not records:
        errors.append(f"{prefix}: SKU Code '{sku_code}' does not exist.")
        return None
    if len(records) > 1:
        errors.append(f"{prefix}: SKU Code '{sku_code}' is not unique.")
        return None

    sku = records[0]
    if not frappe.has_permission("SKU", "write", sku.name):
        errors.append(f"{prefix}: you do not have permission to update SKU Code '{sku_code}'.")
        return None
    return sku


def _validate_sku_link(sku_meta, fieldname, value, prefix, errors):
    field = sku_meta.get_field(fieldname)
    if not field or field.fieldtype != "Link" or not field.options:
        errors.append(f"{prefix}: SKU field '{fieldname}' is not configured as a linked record.")
        return False
    _validate_link_value(field.options, value, field.label or fieldname, prefix, errors)
    return True


def _validate_sku_numeric_field(sku_meta, fieldname, prefix, errors):
    field = sku_meta.get_field(fieldname)
    if not field or field.fieldtype not in {"Currency", "Float", "Int"}:
        errors.append(f"{prefix}: SKU field '{fieldname}' is not configured as a numeric field.")
        return False
    return True


def _validate_link_value(doctype, value, label, prefix, errors):
    if not frappe.db.exists(doctype, value):
        errors.append(f"{prefix}: {label} '{value}' does not exist in {doctype}.")
    elif not frappe.has_permission(doctype, "read", value):
        errors.append(f"{prefix}: you do not have permission to read {doctype} '{value}'.")


def _validate_reference_value(value, current_value, label, prefix, errors):
    supplied = _text(value)
    if supplied and supplied != (current_value or ""):
        errors.append(
            f"{prefix}: {label} '{supplied}' does not match the current SKU value '{current_value or ''}'."
        )


def _validate_linked_sku_detail_is_unambiguous(item, errors):
    try:
        _linked_sku_detail_names(item)
    except ValueError as error:
        errors.append(f"SKU Code '{item['sku_code']}': {error}")


def _linked_sku_detail_names(item):
    """Find a single safe SKU Details row to receive a generated breakup reference."""
    sku_master = item["sku_master"]
    if not sku_master:
        return []

    exact_matches = frappe.get_all(
        "SKU Details", filters={"parent": sku_master, "sku": item["sku_code"]}, pluck="name"
    )
    if len(exact_matches) > 1:
        raise ValueError("more than one SKU Details row matches this SKU code.")
    if exact_matches:
        return exact_matches

    breakup_ref = item.get("breakup_ref")
    if breakup_ref:
        reference_matches = frappe.get_all(
            "SKU Details", filters={"parent": sku_master, "breakup_ref": breakup_ref}, pluck="name"
        )
        if len(reference_matches) > 1:
            raise ValueError("more than one SKU Details row matches the current breakup reference.")
        if reference_matches:
            return reference_matches

    all_matches = frappe.get_all("SKU Details", filters={"parent": sku_master}, pluck="name")
    return all_matches if len(all_matches) == 1 else []


def _synchronise_breakup_reference(item, breakup_ref):
    """Keep SKU and its unambiguous linked SKU Details row aligned with a new ref."""
    if not breakup_ref:
        frappe.throw(f"SKU Code '{item['sku_code']}': breakup save did not return a breakup reference.")

    current_reference = item.get("breakup_ref")
    if current_reference == breakup_ref:
        return

    if not frappe.has_permission("SKU Master", "write", item["sku_master"]):
        frappe.throw(f"You do not have permission to update SKU Master '{item['sku_master']}'.")

    frappe.db.set_value("SKU", item["sku_name"], "breakup_ref", breakup_ref, update_modified=False)
    for detail_name in _linked_sku_detail_names(item):
        frappe.db.set_value("SKU Details", detail_name, "breakup_ref", breakup_ref, update_modified=False)


def _read_sheet(sheet, required_headers, errors):
    rows = list(sheet.iter_rows())
    if not rows:
        errors.append(f"{sheet.title} is empty.")
        return []

    header_cells = rows[0]
    if any(cell.data_type == "f" for cell in header_cells):
        errors.append(f"{sheet.title}: formulas are not allowed in headers.")
        return []
    headers = [_text(cell.value) for cell in header_cells]
    duplicates = sorted({header for header in headers if header and headers.count(header) > 1})
    if duplicates:
        errors.append(f"{sheet.title}: duplicate headers: {', '.join(duplicates)}.")
        return []

    missing = [header for header in required_headers if header not in headers]
    unexpected = [header for header in headers if header and header not in required_headers]
    if missing:
        errors.append(f"{sheet.title}: missing headers: {', '.join(missing)}.")
    if unexpected:
        errors.append(f"{sheet.title}: unsupported headers: {', '.join(unexpected)}.")
    if missing or unexpected:
        return []

    output = []
    for row_index, cells in enumerate(rows[1:], start=2):
        if any(cell.data_type == "f" for cell in cells):
            errors.append(f"{sheet.title} row {row_index}: formulas are not allowed in import data.")
            continue
        values = [cell.value for cell in cells]
        if not any(_text(value) for value in values):
            continue
        output.append((row_index, {header: cells[index].value for index, header in enumerate(headers)}))
    return output


def _load_import_workbook(content):
    _, load_workbook, _, _, _ = _openpyxl()
    return load_workbook(io.BytesIO(content), read_only=True, data_only=False)


def _get_upload_content(file_url):
    if not file_url:
        frappe.throw("Please upload an .xlsx file.")
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_doc.check_permission("read")
    if not str(file_doc.file_name or file_doc.file_url).lower().endswith(".xlsx"):
        frappe.throw("Only .xlsx files can be imported.")
    content = file_doc.get_content()
    if isinstance(content, str):
        content = content.encode()
    if not content:
        frappe.throw("The uploaded file is empty.")
    if len(content) > MAX_IMPORT_BYTES:
        frappe.throw("The uploaded file is larger than the 10 MB import limit.")
    return content, file_doc


def _parse_filters(filters):
    if not filters:
        return {}
    if isinstance(filters, str):
        return frappe.parse_json(filters)
    return filters


def _select_options(field):
    if not field:
        return []
    return [option.strip() for option in (field.options or "").split("\n") if option.strip()]


def _number(value, label, errors):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        errors.append(f"{label} must be a number.")
        return None
    try:
        parsed = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        errors.append(f"{label} must be a valid number.")
        return None
    if not parsed.is_finite():
        errors.append(f"{label} must be a finite number.")
        return None
    return float(parsed)


def _row_number(value, prefix, errors):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    number = _number(value, f"{prefix}: Row No.", errors)
    if number is None:
        return None
    if not number.is_integer() or number < 1:
        errors.append(f"{prefix}: Row No. must be a positive whole number.")
        return None
    return int(number)


def _yes_no(value, prefix, errors):
    text = _text(value).lower()
    if not text or text in {"no", "n", "false", "0"}:
        return False
    if text in {"yes", "y", "true", "1"}:
        return True
    errors.append(f"{prefix}: Update Breakup Details must be Yes or No.")
    return False


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _breakup_summary(rows):
    summaries = []
    for row in rows:
        attribute_type = row.get("attribute_type") or ""
        attribute_value = row.get("attribute_value") or ""
        label = f"{attribute_type}: {attribute_value}".strip(": ")
        details = []
        if row.get("weight") not in (None, ""):
            weight = _display_number(row.get("weight"))
            details.append(f"{weight} {row.get('unit') or ''}".strip())
        if row.get("price") not in (None, ""):
            details.append(f"₹{float(row.get('price')):,.2f}".rstrip("0").rstrip("."))
        summaries.append(f"{label} ({', '.join(details)})" if details else label)
    return " | ".join(summary for summary in summaries if summary)


def _display_number(value):
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:g}"


def _write_table(sheet, headers, rows, editable_headers, Alignment, Font, PatternFill):
    header_fill = PatternFill("solid", fgColor="1F4E78")
    editable_fill = PatternFill("solid", fgColor="FFF2CC")
    internal_fill = PatternFill("solid", fgColor="E7E6E6")
    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=column, value=header)
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for row_index, values in enumerate(rows, start=2):
        for column, value in enumerate(values, start=1):
            header = headers[column - 1]
            cell = sheet.cell(row=row_index, column=column, value=_excel_safe(value))
            cell.alignment = Alignment(vertical="top", wrap_text=header in {"Warehouse", "Breakup Summary"})
            if header in editable_headers:
                cell.fill = editable_fill
            elif header in {"SKU Master", "Breakup Ref", "Breakup Summary", "Row No."}:
                cell.fill = internal_fill

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{_excel_column(len(headers))}{max(1, len(rows) + 1)}"
    widths = {header: max(12, min(36, len(header) + 4)) for header in headers}
    widths.update({"Warehouse": 28, "Breakup Summary": 52, "SKU Code": 20, "SKU Master": 22, "Breakup Ref": 18})
    for column, header in enumerate(headers, start=1):
        sheet.column_dimensions[_excel_column(column)].width = widths[header]
    sheet.row_dimensions[1].height = 28


def _write_instructions(sheet, Alignment, Font, PatternFill):
    rows = [
        ["SKU + Breakup Import Instructions"],
        ["Use the exported workbook as the import source. Keep the three sheet names and all headers unchanged."],
        ["SKU Summary: edit only Metal, Supplier, Cost Price, Selling Price, and Update Breakup Details."],
        ["Blank editable SKU fields do not overwrite the current SKU value. A numeric zero is a valid price."],
        ["Breakup Details: edit Attribute Type, Attribute Value, Weight, Price, and Unit. Add or remove rows only for SKUs whose Update Breakup Details value is Yes."],
        ["Update Breakup Details = Yes replaces all current breakup rows for that SKU with the rows in Breakup Details."],
        ["Warning: when Update Breakup Details is Yes and there are no Breakup Details rows for that SKU, the existing breakup rows will be cleared."],
        ["SKU Code identifies the target SKU. SKU Master and Breakup Ref are checked against the current record and are never taken from edited workbook values."],
        ["Item, Warehouse, Weight, Qty, Status, Breakup Summary, and Row No. are report/reference values and are not updated by import."],
    ]
    title_fill = PatternFill("solid", fgColor="1F4E78")
    warning_fill = PatternFill("solid", fgColor="FCE4D6")
    for row_index, row in enumerate(rows, start=1):
        cell = sheet.cell(row=row_index, column=1, value=row[0])
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if row_index == 1:
            cell.font = Font(color="FFFFFF", bold=True, size=14)
            cell.fill = title_fill
            sheet.row_dimensions[row_index].height = 28
        elif row_index == 7:
            cell.fill = warning_fill
            cell.font = Font(bold=True)
        else:
            sheet.row_dimensions[row_index].height = 34
    sheet.column_dimensions["A"].width = 118


def _excel_safe(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def _excel_column(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cache_key(token):
    return f"{CACHE_PREFIX}:{frappe.session.user}:{token}"


def _format_errors(errors):
    return "<br>".join(f"• {escape_html(error)}" for error in errors)


def _openpyxl():
    try:
        from openpyxl import Workbook, load_workbook
        from openpyxl.styles import Alignment, Font, PatternFill
    except ImportError as error:
        frappe.throw(f"The Excel import/export dependency is unavailable: {error}")
    return Workbook, load_workbook, Alignment, Font, PatternFill
