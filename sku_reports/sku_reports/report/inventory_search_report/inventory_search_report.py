import frappe

def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


# =========================
# COLUMNS (UNCHANGED)
# =========================
def get_columns():
    return [

        {
            "label": "SKU Code",
            "fieldname": "sku_code",
            "fieldtype": "Link",
            "options": "SKU",
            "width": 170
        },

        {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 140},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 120},
        {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 100},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 110},

        {"label": "Image", "fieldname": "image_html", "fieldtype": "HTML", "width": 120},

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]


# =========================
# GET CHILD WAREHOUSES (NEW)
# =========================
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


from frappe.utils import flt
def get_batch_stock_balances(sku_codes):
    if not sku_codes:
        return {}

    rows = frappe.db.sql("""
        SELECT
            name,
            batch_id,
            batch_qty
        FROM `tabBatch`
        WHERE (name IN %(sku_codes)s OR batch_id IN %(sku_codes)s)
        AND IFNULL(disabled, 0) = 0
    """, {
        "sku_codes": tuple(sku_codes)
    }, as_dict=True)

    balances = {}

    for row in rows:
        balance_qty = flt(row.batch_qty)

        if row.name:
            balances[row.name] = balance_qty

        if row.batch_id:
            balances[row.batch_id] = balance_qty

    return balances

def get_data(filters):
    conditions = " WHERE 1=1 "
    values = {}

    if filters.get("sku_code"):
        conditions += " AND sku_code = %(sku_code)s"
        values["sku_code"] = filters["sku_code"]

    if filters.get("metal"):
        conditions += " AND metal = %(metal)s"
        values["metal"] = filters["metal"]

    if filters.get("warehouse"):
        child_wh = get_child_warehouses(filters.get("warehouse"))

        if child_wh:
            conditions += " AND warehouse IN %(warehouses)s"
            values["warehouses"] = tuple(child_wh)
        else:
            conditions += " AND warehouse = %(warehouse)s"
            values["warehouse"] = filters["warehouse"]

    rows = frappe.db.sql(f"""
        SELECT
            sku_code,
            product,
            warehouse,
            metal,
            qty,
            cost_price,
            selling_price,
            image_url,
            status
        FROM `tabSKU`
        {conditions}
        ORDER BY modified DESC
    """, values, as_dict=True)

    sku_codes = [d.sku_code for d in rows if d.sku_code]
    stock_balances = get_batch_stock_balances(sku_codes)

    filtered_data = []

    for d in rows:
        stock_balance_qty = stock_balances.get(d.sku_code, 0)

        if stock_balance_qty <= 0:
            continue

        img = d.get("image_url")

        if img:
            d["image_html"] = f"""
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
        else:
            d["image_html"] = "<span style='color:gray'>No Image</span>"

        filtered_data.append(d)

    return filtered_data

# =========================
# DATA
# =========================
# def get_data(filters):
#     conditions = """
#         WHERE 1=1
#         AND (
#             SELECT COALESCE(SUM(sle.actual_qty), 0)
#             FROM `tabStock Ledger Entry` sle
#             WHERE sle.batch_no = `tabSKU`.sku_code
#             AND sle.is_cancelled = 0
#         ) > 0
#     """
#     values = {}

#     if filters.get("sku_code"):
#         conditions += " AND sku_code = %(sku_code)s"
#         values["sku_code"] = filters["sku_code"]

#     if filters.get("metal"):
#         conditions += " AND metal = %(metal)s"
#         values["metal"] = filters["metal"]

#     if filters.get("warehouse"):
#         child_wh = get_child_warehouses(filters.get("warehouse"))

#         if child_wh:
#             conditions += " AND warehouse IN %(warehouses)s"
#             values["warehouses"] = tuple(child_wh)
#         else:
#             conditions += " AND warehouse = %(warehouse)s"
#             values["warehouse"] = filters["warehouse"]


#     if filters.get("status"):
#         conditions += " AND status = %(status)s"
#         values["status"] = filters["status"]


#     data = frappe.db.sql(f"""
#         SELECT
#             sku_code,
#             product,
#             warehouse,
#             metal,
#             qty,
#             cost_price,
#             selling_price,
#             image_url,
#             status
#         FROM `tabSKU`
#         {conditions}
#         ORDER BY modified DESC
#     """, values, as_dict=True)


#     # =========================
#     # IMAGE WITH CLICK SUPPORT (UNCHANGED)
#     # =========================
#     for d in data:
#         img = d.get("image_url")

#         if img:
#             d["image_html"] = f"""
#                 <img src="{img}"
#                     class="sku-popup-img"
#                     style="
#                         height:25px;
#                         width:120px;
#                         object-fit:contain;
#                         border-radius:6px;
#                         border:1px solid #ddd;
#                         background:#fff;
#                         cursor:pointer;
#                     ">
#             """
#         else:
#             d["image_html"] = "<span style='color:gray'>No Image</span>"

#     return data

