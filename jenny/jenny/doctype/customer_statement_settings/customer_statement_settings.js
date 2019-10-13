// Copyright (c) 2019, Nick and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Statement Settings', {
	refresh: function(frm) {

	},
	send_emails_now: function(frm){
		frappe.call({
			method: "send_customer_statement",
			doc: frm.doc,
			callback: function(r) {
				console.log(r);
			}
		});
	}
});
