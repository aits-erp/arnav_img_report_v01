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


# =========================
# DATA
# =========================
def get_data(filters):
    conditions = " WHERE 1=1 "
    values = {}

    if filters.get("sku_code"):
        conditions += " AND sku_code = %(sku_code)s"
        values["sku_code"] = filters["sku_code"]

    if filters.get("metal"):
        conditions += " AND metal = %(metal)s"
        values["metal"] = filters["metal"]

    # =========================
    # ✅ UPDATED WAREHOUSE LOGIC
    # =========================
    if filters.get("warehouse"):

        child_wh = get_child_warehouses(filters.get("warehouse"))

        if child_wh:
            conditions += " AND warehouse IN %(warehouses)s"
            values["warehouses"] = tuple(child_wh)
        else:
            conditions += " AND warehouse = %(warehouse)s"
            values["warehouse"] = filters["warehouse"]


    if filters.get("status"):
        conditions += " AND status = %(status)s"
        values["status"] = filters["status"]


    data = frappe.db.sql(f"""
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


    # =========================
    # IMAGE WITH CLICK SUPPORT (UNCHANGED)
    # =========================
    for d in data:
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

    return data



    # just want to updated that why added comment