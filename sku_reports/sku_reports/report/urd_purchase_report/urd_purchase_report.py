# import frappe
# from frappe.utils import flt, nowdate

# def execute(filters=None):
#     filters = filters or {}

#     if not filters.get("from_date"):
#         filters["from_date"] = nowdate()
#     if not filters.get("to_date"):
#         filters["to_date"] = nowdate()

#     columns = get_columns()
#     data = []

#     # -------------------------
#     # SECTION: URD PURCHASE REPORT
#     # -------------------------
#     rows = get_urd_rows(filters)

#     for row in rows:
#         data.append(row)

#     # -------------------------
#     # TOTAL ROW
#     # -------------------------
#     data.append({})
#     total_amount = sum(flt(d.get("amount")) for d in rows)

#     data.append({
#         "customer_id": "TOTAL",
#         "amount":      total_amount
#     })

#     return columns, data


# # -----------------------------
# # COLUMNS
# # -----------------------------
# def get_columns():
#     return [
#         {"label": "Date",        "fieldname": "date",        "fieldtype": "Date",    "width": 140},
#         {"label": "Customer ID", "fieldname": "customer_id", "fieldtype": "Data",    "width": 180},
#         {"label": "CN No",       "fieldname": "cn_no",       "fieldtype": "Data",    "width": 150},
#         {"label": "Metal",       "fieldname": "metal",       "fieldtype": "Data",    "width": 120},
#         {"label": "Gram",        "fieldname": "gram",        "fieldtype": "Float",   "width": 100},
#         {"label": "Amount",      "fieldname": "amount",      "fieldtype": "Currency","width": 120},
#     ]


# # -----------------------------
# # URD PURCHASE ROWS
# # (field mapping to be added later)
# # -----------------------------
# def get_urd_rows(filters):
#     # TODO: map fields from POS doctype
#     return []import frappe
# from frappe.utils import flt, nowdate

# def execute(filters=None):
#     filters = filters or {}

#     if not filters.get("from_date"):
#         filters["from_date"] = nowdate()
#     if not filters.get("to_date"):
#         filters["to_date"] = nowdate()

#     columns = get_columns()
#     data = []

#     # -------------------------
#     # SECTION: URD PURCHASE REPORT
#     # -------------------------
#     rows = get_urd_rows(filters)

#     for row in rows:
#         data.append(row)

#     # -------------------------
#     # TOTAL ROW
#     # -------------------------
#     data.append({})
#     total_amount = sum(flt(d.get("amount")) for d in rows)

#     data.append({
#         "customer_id": "TOTAL",
#         "amount":      total_amount
#     })

#     return columns, data


# # -----------------------------
# # COLUMNS
# # -----------------------------
# def get_columns():
#     return [
#         {"label": "Date",        "fieldname": "date",        "fieldtype": "Date",    "width": 140},
#         {"label": "Customer ID", "fieldname": "customer_id", "fieldtype": "Data",    "width": 180},
#         {"label": "CN No",       "fieldname": "cn_no",       "fieldtype": "Data",    "width": 150},
#         {"label": "Metal",       "fieldname": "metal",       "fieldtype": "Data",    "width": 120},
#         {"label": "Gram",        "fieldname": "gram",        "fieldtype": "Float",   "width": 100},
#         {"label": "Amount",      "fieldname": "amount",      "fieldtype": "Currency","width": 120},
#     ]


# # -----------------------------
# # URD PURCHASE ROWS
# # (field mapping to be added later)
# # -----------------------------
# def get_urd_rows(filters):
#     # TODO: map fields from POS doctype
#     return []
import frappe
from frappe.utils import flt, nowdate

def execute(filters=None):
    filters = filters or {}

    if not filters.get("from_date"):
        filters["from_date"] = nowdate()
    if not filters.get("to_date"):
        filters["to_date"] = nowdate()

    columns = get_columns()
    data = []

    # -------------------------
    # SECTION: URD PURCHASE REPORT
    # -------------------------
    rows = get_urd_rows(filters)

    for row in rows:
        data.append(row)

    # -------------------------
    # TOTAL ROW
    # -------------------------
    data.append({})
    total_amount = sum(flt(d.get("amount")) for d in rows)

    data.append({
        "customer_id": "TOTAL",
        "amount":      total_amount
    })

    return columns, data


# -----------------------------
# COLUMNS
# -----------------------------
def get_columns():
    return [
        {"label": "Date",        "fieldname": "date",        "fieldtype": "Date",     "width": 140},
        {"label": "Customer ID", "fieldname": "customer_id", "fieldtype": "Data",     "width": 180},
        {"label": "CN No",       "fieldname": "cn_no",       "fieldtype": "Data",     "width": 150},
        {"label": "Metal",       "fieldname": "metal",       "fieldtype": "Data",     "width": 120},
        {"label": "Gross Wt",    "fieldname": "gross_wt",    "fieldtype": "Float",    "width": 100},
        {"label": "Net Wt",      "fieldname": "net_wt",      "fieldtype": "Float",    "width": 100},
        {"label": "Purity",      "fieldname": "purity",      "fieldtype": "Float",    "width": 100},
        {"label": "Amount",      "fieldname": "amount",      "fieldtype": "Currency", "width": 120},
    ]


# -----------------------------
# URD PURCHASE ROWS
# (field mapping to be added later)
# -----------------------------
def get_urd_rows(filters):
    # TODO: map fields from POS doctype
    return []