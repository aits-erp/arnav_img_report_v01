frappe.query_reports["Inventory Search Report"] = {
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
            fieldname: "supplier",
            label: "Supplier",
            fieldtype: "Link",
            options: "Supplier"
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
        },
        {
            fieldname: "purchase_received_date",
            label: "Purchase Received Date",
            fieldtype: "Date"
        }
    ],

    onload: function (report) {
        setTimeout(() => {
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

            if (!document.getElementById("inventory-search-report-style")) {
                const style = document.createElement("style");
                style.id = "inventory-search-report-style";
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

                    .inventory-breakup-button {
                        white-space: nowrap;
                    }
                `;
                document.head.appendChild(style);
            }

            // Bind once even when the report is refreshed.
            if (window.inventorySearchReportHandlersBound) {
                return;
            }

            window.inventorySearchReportHandlersBound = true;

            document.addEventListener("click", function (e) {
                if (e.target.classList.contains("sku-popup-img")) {
                    const modal = document.getElementById("img-preview-modal");
                    const imgTag = document.getElementById("img-preview-tag");

                    imgTag.src = e.target.src;
                    modal.style.display = "block";
                    return;
                }

                if (e.target.classList.contains("img-preview-overlay")) {
                    document.getElementById("img-preview-modal").style.display = "none";
                    return;
                }

                const breakupButton = e.target.closest(".inventory-breakup-button");

                if (!breakupButton) {
                    return;
                }

                const skuMaster = breakupButton.dataset.skuMaster;
                const breakupRef = breakupButton.dataset.breakupRef;

                frappe.call({
                    method: "arnav_customization.arnav_customization.doctype.sku_master.sku_master.get_breakup_rows",
                    args: {
                        sku_master: skuMaster,
                        breakup_ref: breakupRef
                    },
                    freeze: true,
                    freeze_message: __("Loading breakup details..."),
                    callback: function (r) {
                        const breakupRows = r.message || [];

                        const dialog = new frappe.ui.Dialog({
                            title: __("Breakup Details"),
                            size: "extra-large",
                            fields: [
                                {
                                    fieldname: "breakup_table",
                                    label: __("Breakup Details"),
                                    fieldtype: "Table",
                                    read_only: 1,
                                    cannot_add_rows: true,
                                    cannot_delete_rows: true,
                                    in_place_edit: false,
                                    data: breakupRows,
                                    get_data: () => breakupRows,
                                    fields: [
                                        {
                                            fieldname: "attribute_type",
                                            label: __("Attribute Type"),
                                            fieldtype: "Data",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                        {
                                            fieldname: "attribute_value",
                                            label: __("Attribute Value"),
                                            fieldtype: "Data",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                        {
                                            fieldname: "weight",
                                            label: __("Weight"),
                                            fieldtype: "Float",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                        {
                                            fieldname: "price",
                                            label: __("Price"),
                                            fieldtype: "Currency",
                                            in_list_view: 1,
                                            read_only: 1
                                        },
                                        {
                                            fieldname: "unit",
                                            label: __("Unit"),
                                            fieldtype: "Data",
                                            in_list_view: 1,
                                            read_only: 1
                                        }
                                    ]
                                }
                            ]
                        });

                        dialog.show();

                        if (!breakupRows.length) {
                            frappe.show_alert({
                                message: __("No breakup details found for this SKU."),
                                indicator: "orange"
                            });
                        }
                    }
                });
            });
        }, 800);
    }
};