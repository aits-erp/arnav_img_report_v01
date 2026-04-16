// frappe.query_reports["SKU List Report"] = {
//     "filters": [
//         {
//             "fieldname": "sku_code",
//             "label": "SKU Code",
//             "fieldtype": "Link",
//             "options": "SKU"
//         },
//         {
//             "fieldname": "metal",
//             "label": "Metal",
//             "fieldtype": "Link",
//             "options": "Metal Master"
//         },
//         {
//             "fieldname": "supplier",
//             "label": "Supplier",
//             "fieldtype": "Link",
//             "options": "Supplier"
//         },
//         {
//             "fieldname": "warehouse",
//             "label": "Warehouse",
//             "fieldtype": "Link",
//             "options": "Warehouse"
//         },
//         {
//             "fieldname": "status",
//             "label": "Status",
//             "fieldtype": "Select",
//             "options": "\nAvailable\nSold"
//         }
//     ]
// };



frappe.query_reports["SKU List Report"] = {
    filters: [
        {
            fieldname: "sku_code",
            label: "SKU Code",
            fieldtype: "Link",
            options: "SKU"
        },
        {
            fieldname: "metal",
            label: "Metal",
            fieldtype: "Link",
            options: "Metal Master"
        },
        {
            fieldname: "warehouse",
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse"
        },
        {
            fieldname: "status",
            label: "Status",
            fieldtype: "Select",
            options: "\nAvailable\nSold"
        }
    ],

    onload: function(report) {
        setTimeout(() => {
            const style = document.createElement("style");
            style.innerHTML = `
                .dt-row {
                    height: 150px !important;
                }

                .dt-cell {
                    height: 150px !important;
                    vertical-align: middle !important;
                }

                .dt-scrollable {
                    overflow: visible !important;
                }
            `;
            document.head.appendChild(style);
        }, 800);
    }
};