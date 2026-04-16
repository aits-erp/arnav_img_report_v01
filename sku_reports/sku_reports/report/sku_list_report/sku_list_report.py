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
#         {"label": "SKU Code", "fieldname": "sku_code", "fieldtype": "Data", "width": 130},
#         {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 140},
#         {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 120},
#         {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 100},
#         {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
#         {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
#         {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 110},

#         # ✅ IMPORTANT: MUST BE HTML
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
#             # ensure proper format
#             img_url = img

#             d["image_html"] = f"""
#                 <img src="{img_url}"
#                     style="
#                         height:55px;
#                         width:55px;
#                         object-fit:cover;
#                         border-radius:6px;
#                         border:1px solid #ddd;
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


# ==========================================================
# COLUMNS
# ==========================================================
def get_columns():
    return [

        # ✅ CHANGED:
        # Data -> Link
        # This makes SKU Code clickable and opens SKU document
        {
            "label": "SKU Code",
            "fieldname": "sku_code",
            "fieldtype": "Link",
            "options": "SKU",
            "width": 150
        },

        {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 160},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 130},
        {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 110},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 120},

        # ✅ HTML image column
        {
            "label": "Image",
            "fieldname": "image_html",
            "fieldtype": "HTML",
            "width": 180
        },

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]


# ==========================================================
# DATA
# ==========================================================
def get_data(filters):
    conditions = " WHERE 1=1 "
    values = {}

    if filters.get("sku_code"):
        conditions += " AND sku_code = %(sku_code)s"
        values["sku_code"] = filters["sku_code"]

    if filters.get("metal"):
        conditions += " AND metal = %(metal)s"
        values["metal"] = filters["metal"]

    if filters.get("supplier"):
        conditions += " AND supplier = %(supplier)s"
        values["supplier"] = filters["supplier"]

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

    # ==========================================================
    # IMAGE RENDER
    # ==========================================================
    for d in data:
        img = d.get("image_url")

        if img:
            d["image_html"] = f"""
                <div style="
                    width:150px;
                    height:120px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    border:1px solid #ddd;
                    border-radius:8px;
                    background:#fff;
                    padding:4px;
                ">
                    <img src="{img}"
                        style="
                            max-width:100%;
                            max-height:100%;
                            width:auto;
                            height:auto;
                            object-fit:contain;
                            border-radius:6px;
                        ">
                </div>
            """
        else:
            d["image_html"] = "<span style='color:gray;'>No Image</span>"

    return data