import frappe
from frappe.model.document import Document
# from datahubv2.core.processor import DataHubProcessor

class DHWebhookInbound(Document):
    pass


# @frappe.whitelist()
# def sync_webhook(inbound_id):
#     webhook = frappe.get_doc("DH Webhook Inbound", {"inbound_id": inbound_id})
#     if webhook:
#         processor = DataHubProcessor()
#         processor.sync_from_webhook(webhook)
#         return True
#     return False