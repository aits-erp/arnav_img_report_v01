frappe.query_reports["URD PURCHASE REPORT"] = {

    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "client_name",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        }
    ],

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Highlight total row
        if (data && data.customer_id === "TOTAL") {
            value = `<b>${value}</b>`;
        }

        return value;
    }
};