# -*- coding: utf-8 -*-
# Copyright (c) 2019, Nick and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import date, datetime
import frappe, json
from frappe.model.document import Document
from frappe.utils import nowdate, add_months, getdate, get_first_day, get_last_day
from frappe.contacts.doctype.contact.contact import get_default_contact
from frappe.core.doctype.communication.email import make
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import execute as account_recv
from erpnext.accounts.report.general_ledger.general_ledger import execute as gl

INDEX_ACCT_REV_CUST = 0
START_FIG = 5

class CustomerStatementSettings(Document):
	def send_customer_statement(self, customer=None):
		if not self.company or not self.receivable_account:
			frappe.throw("Company and Receivable accounts are mandatory to send emails.")

		# month_day = add_months(nowdate(), -1)
		month_day = nowdate()
		first_day = get_first_day(month_day)
		last_day = get_last_day(month_day)	
		month = first_day.strftime("%B")

		account_rev_args = frappe._dict({
			"company": self.company,
			"ageing_based_on":"Posting Date",
			"range1":30,
			"range2":60,
			"range3":90,
			"report_date": last_day
		})

		gl_args = frappe._dict({
			"company": self.company,
			"from_date": first_day,
			"to_date": last_day,
			"party_type":"Customer",
			"account":self.receivable_account,
			"group_by":"Group by Voucher (Consolidated)"
		})
		
		gl_list = filter(self.remove_unwanted_rows, gl(gl_args)[1])
		account_rev_list = account_recv(account_rev_args)

		self.statements = []
		for f in account_rev_list[1]:
			gl_dict = []
			if f[START_FIG] > 0:
				for e in gl_list:
					if f[INDEX_ACCT_REV_CUST] == e.party:
						gl_dict.append(e)
						out_dict = frappe._dict({
							"total": f[START_FIG],
							"30": f[START_FIG+1],
							"60": f[START_FIG+2],
							"90": f[START_FIG+3],
							"90 Above": f[START_FIG+4]
						})
				customer = frappe.get_doc("Customer", e.party)
				contact_link = get_default_contact("Customer", e.party)
				contact = frappe.db.get_value("Contact", contact_link, "email_id")
				
				if contact and hasattr(customer, 'auto_email_statement') and customer.auto_email_statement:
					csdoc = frappe.new_doc("Customer Statement")
					csdoc.customer = e.party
					csdoc.customer_code = customer.customer_code if hasattr(customer, 'customer_code') else ""
					csdoc.customer_email = contact
					csdoc.month = month
					csdoc.gl = json.dumps(gl_dict, default=self.json_serial)
					csdoc.outstanding = json.dumps(out_dict, default=self.json_serial)
					res = csdoc.insert()
					self.statements.append(res)

		frappe.db.commit()
		if len(self.statements) > 0:
			self.send_emails()

		frappe.msgprint("Job is enqued and it will be completed soon.")

	def remove_unwanted_rows(self, data):
		return True if data.account == self.receivable_account else False

	def json_serial(self, obj):    
		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		raise TypeError ("Type %s not serializable" % type(obj))

	def send_emails(self):
		for e in self.statements:
			make(recipients = e.customer_email,
				subject = "Customer Statement for the month of "+e.month,
				content = self.subject,
				doctype = "Customer Statement",
				name = e.name,
				send_email = True,
				send_me_a_copy = False,
				print_format = "Customer Statement",
				read_receipt = False,
				print_letterhead = True)


@frappe.whitelist()
def send_customer_statements():
	d = frappe.get_doc("Customer Statement Settings", "Customer Statement Settings")
	if d.enable_auto_email and getdate().strftime("%-d") == d.send_email_on_date_every_month:
		d.send_customer_statement()
	else:
		frappe.msgprint("Not today")