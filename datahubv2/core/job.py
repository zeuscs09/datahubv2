import frappe
from .processor import DataHubProcessor

def sync_webhook_job(webhook_id):
    """ฟังก์ชันสำหรับเรียกใช้งานในคิว เพื่อประมวลผลข้อมูลจาก webhook"""
    webhook = frappe.get_doc("DH Webhook Inbound", webhook_id)
    processor = DataHubProcessor()
    return processor.sync_from_webhook(webhook)
