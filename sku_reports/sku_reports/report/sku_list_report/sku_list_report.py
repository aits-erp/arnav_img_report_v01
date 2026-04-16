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

        # clickable SKU Code
        {
            "label": "SKU Code",
            "fieldname": "sku_code",
            "fieldtype": "Link",
            "options": "SKU",
            "width": 170
        },

        {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 160},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 150},
        {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 120},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 90},
        {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 130},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 140},

        # bigger image column
        {
            "label": "Image",
            "fieldname": "image_html",
            "fieldtype": "HTML",
            "width": 180
        },

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
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
    # IMAGE HEIGHT = 160
    # ROW HEIGHT automatically grows because content is taller
    # ==========================================================
    for d in data:
        img = d.get("image_url")

        if img:
            d["image_html"] = f"""
                <div style="
                    width:180px;
                    height:160px;
                    min-height:160px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    border:1px solid #dcdcdc;
                    border-radius:8px;
                    background:#fff;
                    padding:6px;
                    overflow:hidden;
                ">
                    <img src="{img}" style="
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
            d["image_html"] = """
                <div style="
                    width:180px;
                    height:160px;
                    min-height:160px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    border:1px solid #dcdcdc;
                    border-radius:8px;
                    background:#fafafa;
                    color:gray;
                ">
                    No Image
                </div>
            """

        # make all text columns vertically centered in taller rows
        for field in [
            "sku_code",
            "product",
            "warehouse",
            "metal",
            "qty",
            "cost_price",
            "selling_price",
            "status"
        ]:
            value = d.get(field) or ""

            d[field] = f"""
                <div style="
                    min-height:160px;
                    display:flex;
                    align-items:center;
                    padding:0 6px;
                ">
                    {value}
                </div>
            """

    return data



# import frappe

# def execute(filters=None):
#     filters = filters or {}

#     columns = get_columns()
#     data = get_data(filters)

#     return columns, data


# ==========================================================
# COLUMNS
# ==========================================================
# def get_columns():
#     return [

#         # ✅ CHANGED:
#         # Data -> Link



#         # This makes SKU Code clickable and opens SKU document
#         {
#             "label": "SKU Code",
#             "fieldname": "sku_code",
#             "fieldtype": "Link",
#             "options": "SKU",
#             "width": 150
#         },

#         {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 160},
#         {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 130},
#         {"label": "Metal", "fieldname": "metal", "fieldtype": "Data", "width": 110},
#         {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
#         {"label": "Cost Price", "fieldname": "cost_price", "fieldtype": "Currency", "width": 110},
#         {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 120},

#         # ✅ HTML image column
#         {
#             "label": "Image",
#             "fieldname": "image_html",
#             "fieldtype": "HTML",
#             "width": 180
#         },

#         {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
#     ]


# # ==========================================================
# # DATA
# # ==========================================================
# def get_data(filters):
#     conditions = " WHERE 1=1 "
#     values = {}

#     if filters.get("sku_code"):
#         conditions += " AND sku_code = %(sku_code)s"
#         values["sku_code"] = filters["sku_code"]

#     if filters.get("metal"):
#         conditions += " AND metal = %(metal)s"
#         values["metal"] = filters["metal"]

#     if filters.get("supplier"):
#         conditions += " AND supplier = %(supplier)s"
#         values["supplier"] = filters["supplier"]

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

#     # ==========================================================
#     # IMAGE RENDER
#     # ==========================================================
#     for d in data:
#         img = d.get("image_url")

#         if img:
#             d["image_html"] = f"""
#                 <div style="
#                     width:150px;
#                     height:120px;
#                     display:flex;
#                     align-items:center;
#                     justify-content:center;
#                     border:1px solid #ddd;
#                     border-radius:8px;
#                     background:#fff;
#                     padding:4px;
#                 ">
#                     <img src="{img}"
#                         style="
#                             max-width:100%;
#                             max-height:100%;
#                             width:auto;
#                             height:auto;
#                             object-fit:contain;
#                             border-radius:6px;
#                         ">
#                 </div>
#             """
#         else:
#             d["image_html"] = "<span style='color:gray;'>No Image</span>"

#     return data