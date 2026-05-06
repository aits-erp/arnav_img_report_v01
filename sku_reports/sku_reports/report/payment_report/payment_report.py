import frappe
from frappe.utils import flt, nowdate

def execute(filters=None):
    filters = filters or {}

    # Default filter (TODAY)
    if not filters.get("from_date"):
        filters["from_date"] = nowdate()
    if not filters.get("to_date"):
        filters["to_date"] = nowdate()

    columns = get_columns()
    data = []

    payments = get_payment_rows(filters)

    # -------------------------
    # SECTION: PAYMENT REPORT
    # -------------------------
    data.append({"date": "PAYMENT REPORT"})

    for row in payments:
        data.append(row)

    # -------------------------
    # SECTION: PAYMENT RECO
    # -------------------------
    data.append({})
    data.append({"date": "PAYMENT RECO"})

    summary = get_payment_summary(payments)
    data.append(summary)

    # -------------------------
    # SECTION: URD PURCHASE
    # (dummy for now)
    # -------------------------
    data.append({})
    data.append({"date": "URD PURCHASE RECO"})

    # 👉 Replace with your actual URD doctype later
    # currently empty

    # -------------------------
    # TOTAL
    # -------------------------
    data.append({})
    total = sum(flt(d.get("amount")) for d in payments)

    data.append({
        "customer": "TOTAL",
        "amount": total
    })

    return columns, data


# -----------------------------
# COLUMNS
# -----------------------------
def get_columns():
    return [
        {"label": "Date", "fieldname": "date", "width": 140},
        {"label": "Customer", "fieldname": "customer", "width": 180},
        {"label": "Invoice", "fieldname": "invoice", "width": 150},
        {"label": "Payment Mode", "fieldname": "mode", "width": 140},
        {"label": "Reference No", "fieldname": "ref", "width": 150},
        {"label": "Amount", "fieldname": "amount", "width": 120},

        # Payment Reco columns
        {"label": "Cash", "fieldname": "cash", "width": 100},
        {"label": "Card", "fieldname": "card", "width": 100},
        {"label": "UPI", "fieldname": "upi", "width": 100},
        {"label": "Credit Note", "fieldname": "credit_note", "width": 120},
        {"label": "Cheque", "fieldname": "cheque", "width": 100},
        {"label": "Advance", "fieldname": "advance", "width": 100},
    ]


# -----------------------------
# PAYMENT ROW DATA
# -----------------------------
def get_payment_rows(filters):
    return frappe.db.sql("""
        SELECT
            DATE(pos.date) as date,
            pos.client_name as customer,
            pos.name as invoice,
            pay.payment_type as mode,
            pay.credit_note as ref,
            pay.amount
        FROM `tabPOS` pos
        INNER JOIN `tabPOS Payment Details` pay
            ON pay.parent = pos.name
        WHERE pos.docstatus = 1
        AND DATE(pos.date) BETWEEN %(from_date)s AND %(to_date)s
        {customer_filter}
        ORDER BY pos.date
    """.format(
        customer_filter="AND pos.client_name = %(client_name)s"
        if filters.get("client_name") else ""
    ), filters, as_dict=1)


# -----------------------------
# PAYMENT SUMMARY
# -----------------------------
def get_payment_summary(rows):
    summary = {
        "cash": 0,
        "card": 0,
        "upi": 0,
        "credit_note": 0,
        "cheque": 0,
        "advance": 0
    }

    for r in rows:
        mode = (r.get("mode") or "").lower()
        amt = flt(r.get("amount"))

        if mode == "cash":
            summary["cash"] += amt
        elif mode == "card":
            summary["card"] += amt
        elif mode == "upi":
            summary["upi"] += amt
        elif mode == "cheque":
            summary["cheque"] += amt
        elif mode == "online":
            summary["upi"] += amt
        elif mode == "gift voucher":
            summary["advance"] += amt
        elif mode == "old gold":
            summary["credit_note"] += amt

    return summary