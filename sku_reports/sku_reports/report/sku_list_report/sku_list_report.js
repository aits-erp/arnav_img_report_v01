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

            /* ✅ Let row expand naturally */
            .dt-row {
                height: auto !important;
            }

            .dt-cell {
                height: auto !important;
                display: flex;
                align-items: center;
            }

            .dt-cell__content {
                height: auto !important;
                white-space: normal !important;
            }

            /* ✅ Image container controls row height */
            .img-cell-wrapper {
                height: 140px;
                width: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            /* ✅ Image fills container */
            .sku-image {
                height: 100%;
                width: 100%;
                object-fit: contain;
                border: 1px solid #ddd;
                border-radius: 6px;
                background: #fff;
            }

            /* No image text */
            .no-image {
                color: #888;
                font-size: 12px;
            }

            `;
            document.head.appendChild(style);
        }, 800);
    }
};