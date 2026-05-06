frappe.query_reports["PAYMENT REPORT"] = {

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

        // Section headers
        if (data && data.date &&
            (data.date === "PAYMENT REPORT" ||
             data.date === "PAYMENT RECO" ||
             data.date === "URD PURCHASE RECO")) {

            value = `<b style="font-size:13px;">${value}</b>`;
        }

        // Highlight total
        if (data && data.customer === "TOTAL") {
            value = `<b>${value}</b>`;
        }

        return value;
    }
};