import frappe
from frappe import _
import json
from datetime import datetime
from datahubv2.core.processor import DataHubProcessor
from datahubv2.core.hook import send_pending_webhook

@frappe.whitelist()
def sync(contact_id):
    processor = DataHubProcessor()
    return processor.sync_from_ic360(contact_id,"MANUAL")

@frappe.whitelist()
def send_outbound():
    send_pending_webhook()
    return "Webhook sent"