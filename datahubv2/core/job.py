import frappe
from .processor import DataHubProcessor
from .hook import send_webhook_data

def sync_webhook_job(webhook_id):
    """ฟังก์ชันสำหรับเรียกใช้งานในคิว เพื่อประมวลผลข้อมูลจาก webhook"""
    webhook = frappe.get_doc("DH Webhook Inbound", webhook_id)
    processor = DataHubProcessor()
    return processor.sync_from_webhook(webhook)

def send_webhook_job():
    """ส่ง webhook ทั้งหมดที่สถานะเป็น Pending"""
    webhooks = frappe.get_all("DH Webhook Outbound", filters={"status": "Pending"}, fields=["name"])
    for webhook in webhooks:
        doc = frappe.get_doc("DH Webhook Outbound", webhook.name)
        # ส่งทันทีแทนการใส่ queue
        send_webhook_data(doc)
        
def send_webhook_job_async():
    """ส่ง webhook ทั้งหมดที่สถานะเป็น Pending แบบ async"""
    try:
        frappe.log_error(
            message="Starting send_webhook_job_async", 
            title="Webhook Job Start"
        )
        
        webhooks = frappe.get_all("DH Webhook Outbound", filters={"status": "Pending"}, fields=["name"])
        
        frappe.log_error(
            message=f"Found {len(webhooks)} pending webhooks: {[w.name for w in webhooks]}", 
            title="Webhook Job Count"
        )
        
        if not webhooks:
            frappe.log_error(
                message="No pending webhooks found", 
                title="Webhook Job No Data"
            )
            return {"status": "success", "message": "No pending webhooks"}
        
        for webhook in webhooks:
            # ส่งแต่ละ webhook ไปยัง queue
            job = frappe.enqueue(
                "datahubv2.core.job.send_single_webhook",
                webhook_name=webhook.name,
                queue="default",
                timeout=300
            )
            
            frappe.log_error(
                message=f"Enqueued webhook {webhook.name} with job ID: {job.id if job else 'None'}", 
                title="Webhook Job Enqueued"
            )
            
        return {"status": "success", "message": f"Enqueued {len(webhooks)} webhooks"}
        
    except Exception as e:
        frappe.log_error(
            message=f"Error in send_webhook_job_async: {str(e)}", 
            title="Webhook Job Error"
        )
        raise e

def send_single_webhook(webhook_name):
    """ส่ง webhook เดียว (สำหรับใช้ใน queue)"""
    doc = frappe.get_doc("DH Webhook Outbound", webhook_name)
    return send_webhook_data(doc)
        
def sync_from_ic360_job():
    """ซิงค์ข้อมูลจาก IC360 ทั้งหมดที่ยังไม่ได้ซิงค์"""
    contacts = frappe.get_all("DH IC360Log", filters={"is_sync": "False"}, fields=["name", "contact_id"])
    for contact in contacts:
        # ส่งไปยัง queue
        frappe.enqueue(
            "datahubv2.core.job.sync_single_ic360",
            contact_id=contact.contact_id,
            log_name=contact.name,
            queue="default",
            timeout=600
        )
        
def sync_single_ic360(contact_id, log_name=None):
    """ซิงค์ข้อมูลจาก IC360 รายการเดียว (สำหรับใช้ใน queue)"""
    try:

        frappe.log_error(message=f"Syncing IC360 for contact {contact_id} log_name: {log_name}", title="sync_single_ic360")
        processor = DataHubProcessor()
        result = processor.sync_from_ic360(contact_id, "JOB")
        
        # อัพเดทสถานะ log ถ้ามี
        if log_name:
            frappe.log_error(message=f"Updating log {log_name} to True", title="sync_single_ic360")
            log_doc = frappe.get_doc("DH IC360Log", log_name)
            log_doc.is_sync = True
            log_doc.sync_result = frappe.as_json(result)
            log_doc.save(ignore_permissions=True)
            
        return result
        
    except Exception as e:
        # อัพเดทสถานะ error ถ้ามี
        if log_name:
            log_doc = frappe.get_doc("DH IC360Log", log_name)
            log_doc.is_sync = False
            log_doc.sync_result = frappe.as_json({"status": "error", "message": str(e)})
            log_doc.save(ignore_permissions=True)
        raise e