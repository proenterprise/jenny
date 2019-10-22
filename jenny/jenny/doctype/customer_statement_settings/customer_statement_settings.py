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
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import execute as accounts_rsumm
from erpnext.accounts.report.general_ledger.general_ledger import execute as gl

class CustomerStatementSettings(Document):
	def send_customer_statement(self, customers=[]):
		if not self.company or not self.receivable_account:
			frappe.throw("Company and Receivable accounts are mandatory to send emails.")

		# month_day = add_months(nowdate(), -1)
		month_day = nowdate()
		first_day = get_first_day(month_day)
		last_day = get_last_day(month_day)
		month = first_day.strftime("%B")

		accounts_rec_args = frappe._dict({
			"company": self.company,
			"ageing_based_on":"Posting Date",
			"range1":30,
			"range2":60,
			"range3":90,
			"range4":120,
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

		gl_rows = filter(self.is_receivable_type, gl(gl_args)[1])
		rec_summaries = accounts_rsumm(accounts_rec_args)[1]
		self.customers = customers
		if len(self.customers) > 0:
			rec_summaries = filter(self.is_customer_type, rec_summaries)

		self.statements = []
		for customer_summary in rec_summaries:
			gl_dict = []
			if customer_summary.outstanding > 0:
				for e in gl_rows:
					if customer_summary.party == e.party:
						gl_dict.append(e)
						out_dict = frappe._dict({
							"total": customer_summary.outstanding,
							"30": customer_summary.range1,
							"60": customer_summary.range2,
							"90": customer_summary.range3,
							"90 Above": customer_summary.range4+customer_summary.range5
						})
				customer = frappe.get_doc("Customer", customer_summary.party)
				contact_link = get_default_contact("Customer", customer_summary.party)
				contact = frappe.db.get_value("Contact", contact_link, "email_id")

				if contact and (not hasattr(customer, 'do_not_email_monthly_statement')
					or (hasattr(customer, 'do_not_email_monthly_statement')
					and not customer.do_not_email_monthly_statement)):
					customer_statement_doc = frappe.new_doc("Customer Statement")
					customer_statement_doc.customer = customer_summary.party
					customer_statement_doc.customer_code = customer.customer_code if hasattr(customer, 'customer_code') else ""
					customer_statement_doc.customer_email = contact
					customer_statement_doc.month = month
					customer_statement_doc.gl = json.dumps(gl_dict, default=self.json_serial)
					customer_statement_doc.outstanding = json.dumps(out_dict, default=self.json_serial)
					insert_statement_doc = customer_statement_doc.insert()
					self.statements.append(insert_statement_doc)

		frappe.db.commit()
		if len(self.statements) > 0:
			self.send_emails()

		frappe.msgprint("Job queued for execution.")

	def is_receivable_type(self, data):
		return True if data.account == self.receivable_account else False

	def is_customer_type(self, data):
		return True if data.party in self.customers else False

	def json_serial(self, obj):
		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		raise TypeError ("Type %s not serializable" % type(obj))


	# Create emails from array of statements
	def send_emails(self):
		customer_statement = []

		for customer_statement in self.statements:
			make(
				recipients = e.customer_email,
				subject = self.company+" Billng for "+e.month,
				content = self.subject,
				doctype = "Customer Statement",
				name = e.name,
				send_email = True,
				send_me_a_copy = False,
				print_format = "Customer Statement",
				read_receipt = False,
				print_letterhead = True
			)


@frappe.whitelist()
def send_customer_statements():
	settings = frappe.get_doc("Customer Statement Settings", "Customer Statement Settings")
	if settings.enable_auto_email and getdate().strftime("%-d") == settings.send_email_on_date_every_month:
		settings.send_customer_statement()
	else:
		frappe.msgprint("Not due")

@frappe.whitelist()
def send_customer_statement_api(customers=[]):
	settings = frappe.get_doc("Customer Statement Settings", "Customer Statement Settings")
	settings.send_customer_statement(customers)
