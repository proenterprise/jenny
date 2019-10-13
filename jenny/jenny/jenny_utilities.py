# -*- coding: utf-8 -*-
# Copyright (c) 2019, GoElite and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import datetime, frappe, redis, ast
from frappe import msgprint, _

class JennyUtilities():
    def send_customer_statement(customer=None):
        frappe.msgprint("Clicked")

