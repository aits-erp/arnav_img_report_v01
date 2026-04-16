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
    "filters": [
        {
            "fieldname": "sku_code",
            "label": "SKU Code",
            "fieldtype": "Link",
            "options": "SKU"
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
    ],

    onload: function(report) {
        setTimeout(() => {

            // ✅ Create popup modal (once)
            if (!document.getElementById("img-preview-modal")) {
                const modal = document.createElement("div");
                modal.id = "img-preview-modal";
                modal.innerHTML = `
                    <div class="img-preview-overlay"></div>
                    <div class="img-preview-content">
                        <img id="img-preview-tag" src="" />
                    </div>
                `;
                document.body.appendChild(modal);
            }

            // ✅ CSS for popup
            const style = document.createElement("style");
            style.innerHTML = `

            #img-preview-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 9999;
            }

            .img-preview-overlay {
                position: absolute;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
            }

            .img-preview-content {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                max-width: 90%;
                max-height: 90%;
            }

            .img-preview-content img {
                width: auto;
                height: auto;
                max-width: 100%;
                max-height: 90vh;
                border-radius: 8px;
                background: #fff;
            }

            `;
            document.head.appendChild(style);

            // ✅ Click event for image
            document.addEventListener("click", function(e) {
                if (e.target.classList.contains("sku-popup-img")) {
                    const modal = document.getElementById("img-preview-modal");
                    const imgTag = document.getElementById("img-preview-tag");

                    imgTag.src = e.target.src;
                    modal.style.display = "block";
                }

                // Close when clicking outside
                if (e.target.classList.contains("img-preview-overlay")) {
                    document.getElementById("img-preview-modal").style.display = "none";
                }
            });

        }, 800);
    }
};