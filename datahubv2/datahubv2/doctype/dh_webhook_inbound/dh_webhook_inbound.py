import frappe
from frappe.model.document import Document
# from datahubv2.core.processor import DataHubProcessor
from datahubv2.lib.pg_connect import log_to_postgres

class DHWebhookInbound(Document):

    def after_insert(self):
        # Parse the JSON payload
        self.payload = frappe.parse_json(self.payload)
        
        # Log webhook inbound data to PostgreSQL
        try:
            log_data = {
                "document_name": self.name,
                "inbound_id": getattr(self, 'inbound_id', None),
                "source_ip": getattr(self, 'source_ip', None),
                "status": getattr(self, 'status', 'Received'),
                "uid": getattr(self, 'uid', None),
                "phonenumber": getattr(self, 'phonenumber', None),
                "firstname": getattr(self, 'firstname', None),
                "lastname": getattr(self, 'lastname', None),
                "line_mid": getattr(self, 'line_mid', None),
                "headers": getattr(self, 'headers', None),
                "payload": self.payload,
                "created_at": getattr(self, 'created_at', frappe.utils.now()),
                "validated_at": getattr(self, 'validated_at', None),
                "processed_at": getattr(self, 'processed_at', None),
                "completed_at": getattr(self, 'completed_at', None),
                "error_message": getattr(self, 'error_message', None),
                "validation_result": getattr(self, 'validation_result', None),
                "logged_by": frappe.session.user,
                "logged_at": frappe.utils.now()
            }
            
            success = log_to_postgres(
                ref_id=self.name,
                ref_module="from_sd",
                json_data=log_data
            )
            
            inbound_ref = getattr(self, 'inbound_id', self.name)
            if success:
                frappe.logger().info(f"Successfully logged webhook inbound: {inbound_ref}")
            else:
                frappe.log_error(f"Failed to log webhook inbound: {inbound_ref}", "PostgreSQL Webhook Log Error")
                
        except Exception as e:
            inbound_ref = getattr(self, 'inbound_id', self.name)
            frappe.log_error(
                f"Exception while logging webhook inbound {inbound_ref}: {str(e)}", 
                "PostgreSQL Webhook Log Exception"
            )


# @frappe.whitelist()
# def sync_webhook(inbound_id):
#     webhook = frappe.get_doc("DH Webhook Inbound", {"inbound_id": inbound_id})
#     if webhook:
#         processor = DataHubProcessor()
#         processor.sync_from_webhook(webhook)
#         return True
#     return False