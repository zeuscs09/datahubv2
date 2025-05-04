import frappe
from datetime import datetime
from ..validator import (
    validate_profile_db_update, validate_child_db_update, 
    validate_campaign_db_update, validate_consent_db_update
)
from ..transformer import (
    transform_contact_for_ic360, transform_line_info_for_ic360, 
    transform_email_for_ic360, transform_mobile_for_ic360,
    transform_nl_ks_contact_for_ic360, transform_address_for_ic360,
    transform_child_for_ic360, transform_child_moreinfo_for_ic360,
    transform_marketing_consent_for_ic360, transform_primary_consent_for_ic360,
    transform_campaign_for_ic360
)

class IC360Processor:
    def __init__(self, parent_processor):
        self.parent = parent_processor
    
    def update_profile(self, profile_data):
        """อัพเดทข้อมูลโปรไฟล์ใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_profile_db_update(profile_data):
                return {"status": "error", "message": "Invalid profile data for IC360 update"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            contact_data = transform_contact_for_ic360(profile_data)
            line_info_data = transform_line_info_for_ic360(profile_data)
            email_data = transform_email_for_ic360(profile_data)
            mobile_data = transform_mobile_for_ic360(profile_data)
            nl_ks_contact_data = transform_nl_ks_contact_for_ic360(profile_data)
            address_data = transform_address_for_ic360(profile_data)
            
            # TODO: ดำเนินการอัพเดทข้อมูลใน IC360 ตามเงื่อนไขการอัพเดทใน 6.1
            # เช่น ในสภาพแวดล้อมการทดสอบ เราอาจจะไม่อัพเดท IC360 จริงๆ แต่บันทึกเป็น log แทน
            frappe.log_error(message=f"IC360 Update: {contact_data}", title="IC360 Update")
            
            return {"status": "success", "message": "IC360 profile updated successfully"}
        except Exception as e:
            frappe.log_error(message=f"IC360 update error: {str(e)}", title="IC360 Update Error")
            return {"status": "error", "message": str(e)}
            
    def update_child(self, child_data):
        """อัพเดทข้อมูลเด็กใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_child_db_update(child_data):
                return {"status": "error", "message": "Invalid child data for IC360 update"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            child_ic360_data = transform_child_for_ic360(child_data)
            child_moreinfo_data = transform_child_moreinfo_for_ic360(child_data)
            
            # TODO: ดำเนินการอัพเดทข้อมูลใน IC360 ตามเงื่อนไขการอัพเดทใน 6.2
            frappe.log_error(message=f"IC360 Child Update: {child_ic360_data}", title="IC360 Child Update")
            
            return {"status": "success", "message": "IC360 child updated successfully"}
        except Exception as e:
            frappe.log_error(message=f"IC360 child update error: {str(e)}", title="IC360 Child Update Error")
            return {"status": "error", "message": str(e)}
            
    def update_consent(self, consent_data):
        """อัพเดทข้อมูลความยินยอมใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_consent_db_update(consent_data):
                return {"status": "error", "message": "Invalid consent data for IC360 update"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            if consent_data.get("consent_type") == "MARKETING":
                consent_ic360_data = transform_marketing_consent_for_ic360(consent_data)
            else:  # PRIVACY
                consent_ic360_data = transform_primary_consent_for_ic360(consent_data)
            
            # TODO: ดำเนินการอัพเดทข้อมูลใน IC360 ตามเงื่อนไขการอัพเดทใน 6.3
            frappe.log_error(message=f"IC360 Consent Update: {consent_ic360_data}", title="IC360 Consent Update")
            
            return {"status": "success", "message": "IC360 consent updated successfully"}
        except Exception as e:
            frappe.log_error(message=f"IC360 consent update error: {str(e)}", title="IC360 Consent Update Error")
            return {"status": "error", "message": str(e)}
            
    def update_campaign(self, campaign_data):
        """อัพเดทข้อมูลแคมเปญใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_campaign_db_update(campaign_data):
                return {"status": "error", "message": "Invalid campaign data for IC360 update"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            campaign_ic360_data = transform_campaign_for_ic360(campaign_data)
            
            # TODO: ดำเนินการอัพเดทข้อมูลใน IC360 ตามเงื่อนไขการอัพเดทใน 6.4
            frappe.log_error(message=f"IC360 Campaign Update: {campaign_ic360_data}", title="IC360 Campaign Update")
            
            return {"status": "success", "message": "IC360 campaign updated successfully"}
        except Exception as e:
            frappe.log_error(message=f"IC360 campaign update error: {str(e)}", title="IC360 Campaign Update Error")
            return {"status": "error", "message": str(e)} 