# import frappe

# def execute(filters=None):
#     filters = filters or {}

#     columns = get_columns()
#     data = get_data(filters)

#     return columns, data


# # =========================
# # COLUMNS
# # =========================
# def get_columns():
#     return [

#         # ✅ CHANGED: clickable SKU Code
#         {
#             "label": "SKU Code",
#             "fieldname": "sku_code",
#             "fieldtype": "Link",
#             "options": "SKU",
#             "width": 170
#         },

#         {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 140},
#         {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 120},
#         {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 100},
#         {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
#         {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
#         {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 110},

#         # ✅ HTML image column
#         {"label": "Image", "fieldname": "image_html", "fieldtype": "HTML", "width": 120},

#         {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
#     ]


# # =========================
# # DATA
# # =========================
# def get_data(filters):
#     conditions = " WHERE 1=1 "
#     values = {}

#     if filters.get("sku_code"):
#         conditions += " AND sku_code = %(sku_code)s"
#         values["sku_code"] = filters["sku_code"]

#     if filters.get("metal"):
#         conditions += " AND metal = %(metal)s"
#         values["metal"] = filters["metal"]

#     if filters.get("warehouse"):
#         conditions += " AND warehouse = %(warehouse)s"
#         values["warehouse"] = filters["warehouse"]

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
#     # IMAGE RENDER FIX
#     # =========================
#     for d in data:
#         img = d.get("image_url")

#         if img:
#             img_url = img

#             d["image_html"] = f"""
#                 <img src="{img_url}"
#                     style="
#                         height:140px;
#                         width:120px;
#                         object-fit:contain;
#                         border-radius:6px;
#                         border:1px solid #ddd;
#                         background:#fff;
#                     ">
#             """
#         else:
#             d["image_html"] = "<span style='color:gray'>No Image</span>"

#     return data





import frappe

def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


# =========================
# COLUMNS
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

        # ✅ Image column (unchanged structure)
        {"label": "Image", "fieldname": "image_html", "fieldtype": "HTML", "width": 120},

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]


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

    if filters.get("warehouse"):
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
    # IMAGE WITH CLICK SUPPORT
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