from __future__ import unicode_literals
from frappe import _

def get_data():

    return [
        {
            "label": _("Document"),
            "icon": "octicon octicon-briefcase",
            "items": [
                {
                    "type": "doctype",
                    "name": "Customer Statement",
                    "label": _("Customer Statement"),
                },
                {
                    "type": "doctype",
                    "name": "Customer Statement Settings",
                    "label": _("Customer Statement Settings"),
                }
            ]
        }
    ]