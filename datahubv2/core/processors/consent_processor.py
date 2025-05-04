import frappe
from datetime import datetime
from ..validator import validate_privacy_consent_data,validate_marketing_consent_data
from ..transformer import transform_consent_data

class ConsentProcessor:
    def __init__(self, parent_processor):
        self.parent = parent_processor
        self.consent_doctype = parent_processor.consent_doctype
    
    def process(self, data, parent_id, consent_type="MARKETING"):
        """ประมวลผลข้อมูลความยินยอม"""
        # บันทึกข้อมูลดิบ
        frappe.log_error(message=f"Processing consent data: {data}, type: {consent_type}", title="DataHub Consent Processing")
        
        if consent_type == "MARKETING":
            frappe.log_error(message=f"Processing marketing consent data: {data}", title="DataHub Consent Processing")
            if validate_marketing_consent_data(data):
                consent_data = transform_consent_data(data, parent_id,"MARKETING")
        elif consent_type == "PRIVACY":
            frappe.log_error(message=f"Processing privacy consent data: {data}", title="DataHub Consent Processing")
            if validate_privacy_consent_data(data):
                consent_data = transform_consent_data(data, parent_id,"PRIVACY")
        if consent_data:
            existing_consent = self.find_consent(consent_data)
            if existing_consent:
                consent_result = self.update_consent(existing_consent, consent_data)
            else:
                consent_result = self.create_consent(consent_data)
        return consent_result
    
    def find_consent(self, consent_data):
        """ค้นหาความยินยอมที่มีอยู่ด้วย composite key:
        parent + consent_type + consent_date
        """
        consent = None
        
        if consent_data.get("contact_id") and consent_data.get("consent_type"):
            try:
                filters = {
                    "contact_id": consent_data["contact_id"],
                    "consent_type": consent_data["consent_type"],
                }
                
                # ถ้ามีวันที่ยินยอม ใช้ในการค้นหาด้วย
                if consent_data.get("consent_date"):
                    filters["consent_date"] = consent_data["consent_date"]
                
                consents = frappe.get_list(
                    self.consent_doctype,
                    filters=filters,
                    fields=["name"]
                )
                
                if consents:
                    consent = frappe.get_doc(self.consent_doctype, consents[0].name)
            except Exception as e:
                frappe.log_error(message=f"Error finding consent: {str(e)}", title="Consent Find Error")
                
        return consent
        
    def update_consent(self, existing_consent, new_data):
        """อัพเดทข้อมูลความยินยอมที่มีอยู่"""
        try:
            for key, value in new_data.items():
                if value is not None:
                    setattr(existing_consent, key, value)
                    
            existing_consent.save(ignore_permissions=True)
            return existing_consent
        except Exception as e:
            frappe.log_error(message=f"Consent update error: {str(e)}", title="Consent Update Error")
            raise e
            
    def create_consent(self, consent_data):
        """สร้างข้อมูลความยินยอมใหม่"""
        try:
            # บันทึก log สำหรับการดีบัก
            frappe.log_error(message=f"Consent data debug: {consent_data}", title="Consent Data Debug")
                
            new_consent = frappe.get_doc({
                "doctype": self.consent_doctype,
                **consent_data
            })
            new_consent.insert(ignore_permissions=True)
            return new_consent
        except Exception as e:
            frappe.log_error(message=f"Consent creation error: {str(e)}", title="Consent Creation Error")
            raise e
    
    def get_last_consent_id(self):
        """ดึงรหัสความยินยอมล่าสุดที่สร้าง"""
        try:
            consents = frappe.get_list(
                self.consent_doctype,
                fields=["name"],
                order_by="creation desc",
                limit=1
            )
            return consents[0].name if consents else None
        except Exception as e:
            frappe.log_error(message=f"Error getting last consent ID: {str(e)}", title="Get Consent ID Error")
            return None 