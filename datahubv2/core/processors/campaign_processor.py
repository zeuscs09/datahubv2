import frappe
from datetime import datetime
from ..validator import validate_campaign_data
from ..transformer import transform_campaign_data

class CampaignProcessor:
    def __init__(self, parent_processor):
        self.parent = parent_processor
        self.campaign_doctype = parent_processor.campaign_doctype
    
    def process(self, data, parent_id):
        """ประมวลผลข้อมูลแคมเปญ"""
        # บันทึกข้อมูลดิบ
        frappe.log_error(message=f"Processing campaign data: {data}", title="DataHub Campaign Processing")
        
        # ตรวจสอบความถูกต้องของข้อมูล
        if not validate_campaign_data(data):
            return {"status": "error", "message": "Invalid campaign data"}
            
        # แปลงข้อมูลให้อยู่ในรูปแบบที่ต้องการ
        campaign_data = transform_campaign_data(data, parent_id)
        
        # ค้นหาแคมเปญที่มีอยู่
        existing_campaign = self.find_campaign(campaign_data)
        
        if existing_campaign:
            # อัพเดทข้อมูลที่มีอยู่
            campaign_result = self.update_campaign(existing_campaign, campaign_data)
        else:
            # สร้างข้อมูลแคมเปญใหม่
            campaign_data["contact_id"] = campaign_data["contact_id"]    
            campaign_result = self.create_campaign(campaign_data)

        
        return campaign_result
            
    def find_campaign(self, campaign_data):
        """ค้นหาแคมเปญที่มีอยู่ด้วย composite key:
        parent + application_code + internal_id + internal_alternate_id
        """
        campaign = None
        
        if campaign_data.get("contact_id") and campaign_data.get("application_code") and campaign_data.get("internal_id"):
            try:
                campaigns = frappe.get_list(
                    self.campaign_doctype,
                    filters={
                        "contact_id": campaign_data["contact_id"],
                        "application_code": campaign_data["application_code"],
                        "internal_id": campaign_data["internal_id"],
                        "internal_alternate_id": campaign_data.get("internal_alternate_id") or ""
                    },
                    fields=["name"]
                )
                
                if campaigns:
                    campaign = frappe.get_doc(self.campaign_doctype, campaigns[0].name)
            except Exception as e:
                frappe.log_error(message=f"Error finding campaign: {str(e)}", title="Campaign Find Error")
                
        return campaign
        
    def update_campaign(self, existing_campaign, new_data):
        """อัพเดทข้อมูลแคมเปญที่มีอยู่"""
        try:
            # ในกรณีของแคมเปญ เราอาจจะต้องการอัพเดทเฉพาะบางฟิลด์ ตามเงื่อนไขในเอกสาร
            existing_campaign.last_update_date = new_data.get("last_update_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            existing_campaign.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            existing_campaign.save(ignore_permissions=True)
            return existing_campaign
        except Exception as e:
            frappe.log_error(message=f"Campaign update error: {str(e)}", title="Campaign Update Error")
            raise e
            
    def create_campaign(self, campaign_data):
        """สร้างข้อมูลแคมเปญใหม่"""
        try:
            # บันทึก log สำหรับการดีบัก
            frappe.log_error(message=f"Campaign data debug: {campaign_data}", title="Campaign Data Debug")
                
            new_campaign = frappe.get_doc({
                "doctype": self.campaign_doctype,
                **campaign_data
            })
            new_campaign.insert(ignore_permissions=True)
            return new_campaign
        except Exception as e:
            frappe.log_error(message=f"Campaign creation error: {str(e)}", title="Campaign Creation Error")
            raise e
    
    def get_last_campaign_id(self):
        """ดึงรหัสแคมเปญล่าสุดที่สร้าง"""
        try:
            campaigns = frappe.get_list(
                self.campaign_doctype,
                fields=["name"],
                order_by="creation desc",
                limit=1
            )
            return campaigns[0].name if campaigns else None
        except Exception as e:
            frappe.log_error(message=f"Error getting last campaign ID: {str(e)}", title="Get Campaign ID Error")
            return None 