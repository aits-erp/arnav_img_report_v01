import frappe
from frappe.utils import flt

def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [

        {
            "label": "SKU Code",
            "fieldname": "sku_code",
            "fieldtype": "Link",
            "options": "SKU",
            "width": 170
        },

        {"label": "Item", "fieldname": "product", "fieldtype": "Data", "width": 140},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 120},
        {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 100},
        *get_weight_columns(),
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 110},

        {"label": "Image", "fieldname": "image_html", "fieldtype": "HTML", "width": 120},

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]


def get_sku_fieldnames():
    return {df.fieldname for df in frappe.get_meta("SKU").fields}


def get_weight_field():
    sku_fields = get_sku_fieldnames()

    for fieldname in ("gross_weight", "net_weight", "weight"):
        if fieldname in sku_fields:
            return fieldname

    return None


def get_weight_columns():
    weight_field = get_weight_field()

    if not weight_field:
        return []

    label = {
        "gross_weight": "Gross Weight",
        "net_weight": "Net Weight",
        "weight": "Weight",
    }.get(weight_field, "Weight")

    return [{"label": label, "fieldname": "weight", "fieldtype": "Float", "width": 100}]


def get_child_warehouses(warehouse):

    wh = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)

    if not wh:
        return []

    children = frappe.db.sql("""
        SELECT name
        FROM `tabWarehouse`
        WHERE lft >= %s AND rgt <= %s AND is_group = 0
    """, (wh.lft, wh.rgt), as_list=1)

    return [c[0] for c in children]


def get_selected_warehouses(filters):
    warehouse = filters.get("warehouse")

    if not warehouse:
        return None

    child_wh = get_child_warehouses(warehouse)

    if child_wh:
        return child_wh

    return [warehouse]


def resolve_sku_filter(sku_code):
    if not sku_code:
        return None

    sku_fields = get_sku_fieldnames()
    lookup_fields = ["name"]

    for fieldname in ("sku_code", "batch_no"):
        if fieldname in sku_fields:
            lookup_fields.append(fieldname)

    select_fields = ", ".join(f"`{fieldname}`" for fieldname in lookup_fields)
    where_parts = [f"`{fieldname}` = %(sku_code)s" for fieldname in lookup_fields]

    rows = frappe.db.sql(f"""
        SELECT {select_fields}
        FROM `tabSKU`
        WHERE {" OR ".join(where_parts)}
    """, {"sku_code": sku_code}, as_dict=True)

    sku_codes = {sku_code}

    for row in rows:
        for fieldname in lookup_fields:
            value = row.get(fieldname)
            if value:
                sku_codes.add(value)

    return list(sku_codes)


def get_current_stock_balances(sku_codes=None, warehouses=None):
    values = {}

    direct_conditions = [
        "sle.docstatus < 2",
        "IFNULL(sle.is_cancelled, 0) = 0",
        "IFNULL(sle.batch_no, '') != ''",
        "IFNULL(sle.serial_and_batch_bundle, '') = ''",
        "IFNULL(batch.disabled, 0) = 0",
    ]
    bundle_conditions = [
        "sle.docstatus < 2",
        "IFNULL(sle.is_cancelled, 0) = 0",
        "sbb.docstatus = 1",
        "sbe.docstatus = 1",
        "IFNULL(sbe.batch_no, '') != ''",
        "IFNULL(batch.disabled, 0) = 0",
    ]

    if sku_codes:
        values["sku_codes"] = tuple(sku_codes)
        direct_conditions.append("sle.batch_no IN %(sku_codes)s")
        bundle_conditions.append("sbe.batch_no IN %(sku_codes)s")

    if warehouses:
        values["warehouses"] = tuple(warehouses)
        direct_conditions.append("sle.warehouse IN %(warehouses)s")
        bundle_conditions.append("sle.warehouse IN %(warehouses)s")

    direct_where = " AND ".join(direct_conditions)
    bundle_where = " AND ".join(bundle_conditions)

    direct_rows = frappe.db.sql(f"""
        SELECT
            sle.batch_no AS sku_code,
            sle.item_code AS product,
            sle.warehouse,
            SUM(sle.actual_qty) AS balance_qty,
            MAX(sle.posting_datetime) AS latest_posting_datetime
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabBatch` batch
            ON batch.name = sle.batch_no
        WHERE {direct_where}
        GROUP BY sle.batch_no, sle.item_code, sle.warehouse
    """, values, as_dict=True)

    bundle_rows = frappe.db.sql(f"""
        SELECT
            sbe.batch_no AS sku_code,
            sle.item_code AS product,
            sle.warehouse,
            SUM(sbe.qty) AS balance_qty,
            MAX(sle.posting_datetime) AS latest_posting_datetime
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabSerial and Batch Entry` sbe
            ON sbe.parent = sle.serial_and_batch_bundle
        INNER JOIN `tabSerial and Batch Bundle` sbb
            ON sbb.name = sbe.parent
        INNER JOIN `tabBatch` batch
            ON batch.name = sbe.batch_no
        WHERE {bundle_where}
        GROUP BY sbe.batch_no, sle.item_code, sle.warehouse
    """, values, as_dict=True)

    balances = {}

    for row in direct_rows + bundle_rows:
        key = (row.sku_code, row.product, row.warehouse)

        if key not in balances:
            balances[key] = frappe._dict({
                "sku_code": row.sku_code,
                "product": row.product,
                "warehouse": row.warehouse,
                "qty": 0,
                "latest_posting_datetime": row.latest_posting_datetime,
            })

        balances[key].qty += flt(row.balance_qty)

        if (
            row.latest_posting_datetime
            and (
                not balances[key].latest_posting_datetime
                or row.latest_posting_datetime > balances[key].latest_posting_datetime
            )
        ):
            balances[key].latest_posting_datetime = row.latest_posting_datetime

    data = [row for row in balances.values() if flt(row.qty) > 0]
    data.sort(key=lambda row: str(row.latest_posting_datetime or ""), reverse=True)

    return data


def get_sku_metadata(sku_codes):
    if not sku_codes:
        return {}

    sku_fields = get_sku_fieldnames()
    optional_fields = [
        "sku_code",
        "batch_no",
        "product",
        "metal",
        "supplier",
        "cost_price",
        "selling_price",
        "image_url",
        "image",
        "status",
        "gross_weight",
        "net_weight",
        "weight",
    ]
    select_fields = ["name", "modified"]
    select_fields.extend([fieldname for fieldname in optional_fields if fieldname in sku_fields])

    where_fields = ["name"]
    for fieldname in ("sku_code", "batch_no"):
        if fieldname in sku_fields:
            where_fields.append(fieldname)

    fields_sql = ", ".join(f"`{fieldname}`" for fieldname in select_fields)
    where_sql = " OR ".join(f"`{fieldname}` IN %(sku_codes)s" for fieldname in where_fields)

    rows = frappe.db.sql(f"""
        SELECT {fields_sql}
        FROM `tabSKU`
        WHERE {where_sql}
        ORDER BY modified DESC
    """, {"sku_codes": tuple(sku_codes)}, as_dict=True)

    metadata = {}

    for row in rows:
        for fieldname in where_fields:
            value = row.get(fieldname)

            if value and value not in metadata:
                metadata[value] = row

    return metadata


def get_image_html(img):
    if not img:
        return "<span style='color:gray'>No Image</span>"

    return f"""
        <img src="{img}"
            class="sku-popup-img"
            style="
                height:25px;
                width:120px;
                object-fit:contain;
                border-radius:6px;
                border:1px solid #ddd;
                background:#fff;
                cursor:pointer;
            ">
    """


def passes_metadata_filters(sku_info, filters):
    if filters.get("metal") and sku_info.get("metal") != filters.get("metal"):
        return False

    if filters.get("supplier") and sku_info.get("supplier") != filters.get("supplier"):
        return False

    return True


def get_data(filters):
    if filters.get("status") and filters.get("status").strip().lower() != "available":
        return []

    sku_codes = resolve_sku_filter(filters.get("sku_code"))
    warehouses = get_selected_warehouses(filters)
    stock_rows = get_current_stock_balances(sku_codes=sku_codes, warehouses=warehouses)
    sku_metadata = get_sku_metadata([row.sku_code for row in stock_rows])
    weight_field = get_weight_field()

    filtered_data = []

    for stock_row in stock_rows:
        sku_info = sku_metadata.get(stock_row.sku_code) or frappe._dict()

        if not passes_metadata_filters(sku_info, filters):
            continue

        row = frappe._dict({
            "sku_code": stock_row.sku_code,
            "product": stock_row.product or sku_info.get("product"),
            "warehouse": stock_row.warehouse,
            "metal": sku_info.get("metal"),
            "qty": stock_row.qty,
            "cost_price": sku_info.get("cost_price"),
            "selling_price": sku_info.get("selling_price"),
            "image_html": get_image_html(sku_info.get("image_url") or sku_info.get("image")),
            "status": "Available",
        })

        if weight_field:
            row["weight"] = sku_info.get(weight_field)

        filtered_data.append(row)

    return filtered_data
