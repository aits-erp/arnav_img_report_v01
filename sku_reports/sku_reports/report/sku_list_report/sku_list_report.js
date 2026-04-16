frappe.query_reports["SKU List Report"] = {
    "filters": [
        {
            "fieldname": "sku_code",
            "label": "SKU Code",
            "fieldtype": "Data"
        },
        {
            "fieldname": "metal",
            "label": "Metal",
            "fieldtype": "Link",
            "options": "Metal Master"
        },
        {
            "fieldname": "supplier",
            "label": "Supplier",
            "fieldtype": "Link",
            "options": "Supplier"
        },
        {
            "fieldname": "warehouse",
            "label": "Warehouse",
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "status",
            "label": "Status",
            "fieldtype": "Select",
            "options": "\nAvailable\nSold"
        }
    ]
};