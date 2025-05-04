import frappe
from frappe import _
import json
from datetime import datetime

@frappe.whitelist()
def profile():
    """Receive profile data via webhook"""
    try:
        # Get request data
        request_data = frappe.request.get_data()
        headers = dict(frappe.request.headers)
        source_ip = frappe.request.remote_addr
        
        # Parse JSON data
        try:
            data = json.loads(request_data)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON format"
            }
        
        # Validate required fields
        required_fields = ["uid", "phonenumber", "firstname", "lastname"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Create webhook inbound record
        webhook = frappe.get_doc({
            "doctype": "DH Webhook Inbound",
            "inbound_id": f"INB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "source_ip": source_ip,
            "status": "Received",
            "created_at": datetime.now(),
            "validated_at": datetime.now(),
            "payload": request_data.decode('utf-8'),
            "headers": json.dumps(headers,indent=4),
            "line_mid": data.get("line_mid"),
            "uid": data.get("uid"),
            "phonenumber": data.get("phonenumber"),
            "firstname": data.get("firstname"),
            "lastname": data.get("lastname"),
            "validation_result": json.dumps({
                "status": "success",
                "message": "Data validated successfully",
                "missing_fields": []
            })
        })
        webhook.insert(ignore_permissions=True)
        frappe.enqueue(
            method="datahubv2.core.job.sync_webhook_job",
            queue="default",
            timeout=300,
            webhook_id=webhook.name
        )
        return {
            "status": "success",
            "message": "Profile received successfully",
            "inbound_id": webhook.inbound_id
        }
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Webhook Profile Error")
        return {
            "status": "error",
            "message": str(e)
        }

