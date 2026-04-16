# Copyright (c) 2026, Sukku and contributors
# For license information, please see license.txt

# import frappe


import frappe

def execute(filters=None):
    columns = [
        {
            "label": "Item",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Image",
            "fieldname": "image_html",
            "fieldtype": "HTML",
            "width": 150
        }
    ]

    data = frappe.db.sql("""
        SELECT
            name,
            item_name,
            image
        FROM `tabItem`
        WHERE image IS NOT NULL
        LIMIT 50
    """, as_dict=1)

    result = []

    for d in data:
        image_html = ""
        if d.image:
            image_html = f'<img src="{d.image}" style="height:60px; width:60px; object-fit:cover; border-radius:6px;" />'

        result.append({
            "item_name": d.item_name,
            "image_html": image_html
        })

    return columns, result