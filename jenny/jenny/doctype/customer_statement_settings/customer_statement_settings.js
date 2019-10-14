// Copyright (c) 2019, Nick and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Statement Settings', {
	refresh: function(frm) {

	},
	send_emails_now: function(frm){
		var p = frm.doc;
		var new_cust_list = p.customer_list.filter(x => !x.processed);
		new_cust_list = new_cust_list.map(x => x.customer)

		frappe.call({
			method: "send_customer_statement",
			doc: frm.doc,
			args: {
				customers: new_cust_list
			},
			callback: function(r) {
				console.log(r);
			}
		});
	}
});
