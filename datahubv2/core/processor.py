import frappe
import json
from datetime import datetime, timedelta
from .processors.profile_processor import ProfileProcessor
from .processors.child_processor import ChildProcessor
from .processors.campaign_processor import CampaignProcessor
from .processors.consent_processor import ConsentProcessor
from .processors.ic360_processor import IC360Processor
from datahub.utils.general import get_lookup_formula,get_lookup_data
from datahub.lib.ic360.client import IC360Client

class DataHubProcessor:
    def __init__(self):
        self.profile_doctype = "ETL Main Profile"
        self.child_doctype = "ETL Child"
        self.campaign_doctype = "ETL Campaign"
        self.consent_doctype = "ETL Consent"
        self.sync_log_doctype = "ETL Sync Log"
        
        # สร้าง processor ย่อยๆ
        self.profile_processor = ProfileProcessor(self)
        self.child_processor = ChildProcessor(self)
        self.campaign_processor = CampaignProcessor(self)
        self.consent_processor = ConsentProcessor(self)
        self.ic360_processor = IC360Processor(self)
        self.ic360_client = IC360Client()
  
   
   
 
    def update_ic360_profile(self, profile_data):
        """อัพเดทข้อมูลโปรไฟล์ใน IC360"""
        return self.ic360_processor.update_profile(profile_data)
        
    def update_ic360_child(self, child_data):
        """อัพเดทข้อมูลเด็กใน IC360"""
        return self.ic360_processor.update_child(child_data)
        
    def update_ic360_consent(self, consent_data):
        """อัพเดทข้อมูลความยินยอมใน IC360"""
        return self.ic360_processor.update_consent(consent_data)
        
    def update_ic360_campaign(self, campaign_data):
        """อัพเดทข้อมูลแคมเปญใน IC360"""
        return self.ic360_processor.update_campaign(campaign_data)
    
    def update_datahub_lookup(self,main_profile,child_data):
        """ค้นหาข้อมูลจาก main profile และ child profile"""
        main_profile.sourceid = get_lookup_data("SD","DataSourceCode",main_profile.data_source_code)

        main_profile.gender = get_lookup_data("SD","GENDER",main_profile.gender_sd)
    
        if main_profile.province_name and main_profile.amphur_name and main_profile.sub_district_name:
            area_info = self.ic360_client.get_area_info(
                province_name=main_profile.province_name,
                amphur_name=main_profile.amphur_name, 
                district_name=main_profile.sub_district_name
            )
            
            if area_info and len(area_info) > 0:
                area = area_info[0]
                main_profile.state_code = area["province_code"]
                main_profile.city = area["amphur_code"]
                main_profile.sub_district = area["district_code"]
                if area["zipcode"] and not main_profile.postal_code:
                    main_profile.postal_code = area["zipcode"]
       
        
        # บันทึก main profile
        main_profile.save(ignore_permissions=True)
        
        # ถ้ามีข้อมูลเด็ก ให้อัพเดทข้อมูล lookup
        if child_data :
            child_profile = child_data
            if child_profile:
                child_profile.birth_plan = get_lookup_data("SD","NL_BIRTH_PLAN",child_profile.gg_child_delivery_type)
                child_profile.born_place_type = get_lookup_data("SD","NL_ANC_PLACE",child_profile.gg_hospital)
                child_profile.mother_stage = get_lookup_data("SD","NL_MOTHERSTAGE",child_profile.child_birthdatereliability)
                lookup_formula = get_lookup_formula("SD", child_profile.gg_milk_currently_consuming) #last formula
                
                if lookup_formula and lookup_formula.value:
                    child_profile.lastpro_key = lookup_formula.value
                    prod_formula = child_profile.lastpro_key.split("-")
                    child_profile.lastpro = prod_formula[0]
                    child_profile.lastformula = prod_formula[1]
                    formula_desc = get_lookup_formula("IC360", prod_formula[0])
                
                frappe.log_error(message=f"child_profile: {child_profile}", title="update_datahub_lookup:child_profile")
                child_profile.save(ignore_permissions=True)
        
    def update_sd_lookup(self,main_profile,child_profile):
        """ค้นหาข้อมูลจาก main profile และ child profile"""
        main_profile.data_source_code = get_lookup_data("IC360","DataSourceCode".main_profile.source_id)
        main_profile.gender_sd  = get_lookup_data("IC360","GENDER",main_profile.gender)
        
        
        child_profile.gg_child_delivery_type  = get_lookup_data("IC360","NL_BIRTH_PLAN",child_profile.birth_plan)
        child_profile.gg_hospital = get_lookup_data("IC360","NL_ANC_PLACE",child_profile.born_place_type )
        child_profile.child_birthdatereliability = get_lookup_data("IC360","NL_MOTHERSTAGE",child_profile.mother_stage )
       
        lastpro_key=child_profile.lastpro + "-" + child_profile.lastformula
        child_profile.gg_milk_currently_consuming = get_lookup_formula("IC360", lastpro_key)
            
        
        main_profile.save(ignore_permissions=True)
        child_profile.save(ignore_permissions=True)
    def sync_from_webhook(self, webhook_doc):
        """ซิงค์ข้อมูลจาก webhook inbound"""
        try:
            # บันทึก log สำหรับการเริ่มต้น sync
            frappe.log_error(message=f"Starting webhook sync for ID: {webhook_doc.name}, inbound_id: {webhook_doc.inbound_id}", title="Webhook Sync Start")
            
            # ดึงข้อมูลจาก webhook
            payload = frappe.parse_json(webhook_doc.payload)
            
            # บันทึก payload สำหรับการดีบัก
            frappe.log_error(message=f"Webhook payload: {payload}", title="Webhook Payload")
            
            child_profiles = []
            # ประมวลผลข้อมูลโปรไฟล์
            profile_result = self.profile_processor.process(payload)
            profile_id = profile_result.contact_id
     
            if not profile_id:
                frappe.log_error(message=f"Profile processing failed: {profile_result.get('message')}", title="Webhook Sync Error")
                return {"status": "error", "message": profile_result.get('message')}
            
            # ประมวลผลข้อมูลเด็ก
            if "child" in payload and isinstance(payload["child"], list):
                # วนลูปเพื่อประมวลผลข้อมูลเด็กแต่ละคน
                for child_item in payload["child"]:
                    child_result = self.child_processor.process(child_item, profile_id)
                
                    child_profiles.append(child_result)
            
            # ประมวลผลข้อมูลแคมเปญ
            if "externalApplication" in payload and isinstance(payload["externalApplication"], list):
                # วนลูปเพื่อประมวลผลข้อมูลแคมเปญแต่ละรายการ
                for campaign_item in payload["externalApplication"]:
                    self.campaign_processor.process(campaign_item, profile_id)
                    
          
            
            # ประมวลผลข้อมูลความยินยอม
            if "Is_MKT_Subscribed":
               
                self.consent_processor.process(payload, profile_id, "MARKETING")
             # ประมวลผลข้อมูลความยินยอม
            if "consent_date":
              
                self.consent_processor.process(payload, profile_id,"PRIVACY")
          
            
            # ตรวจสอบว่ามีข้อมูลเด็กหรือไม่ก่อนส่งไปยังฟังก์ชัน update_datahub_lookup
            frappe.log_error(message=f"child_profiles: {child_profiles}", title="child_profiles")
            if child_profiles and len(child_profiles) > 0:
                # เรียงลำดับข้อมูลเด็กตามวันเกิด (ล่าสุดอยู่ท้ายสุด)
                try:
                    # แก้ไขเป็น
                    sorted_children = sorted([x for x in child_profiles if x is not None], 
                          key=lambda x: x.get("birthdate", "0000-00-00") if x.get("birthdate") else "0000-00-00")
                    last_child = sorted_children[-1]
                    last_child.gg_milk_currently_consuming=profile_result.gg_milk_currently_consuming
                    last_child.gg_child_delivery_type=profile_result.gg_child_delivery_type
                    last_child.gg_hospital=profile_result.gg_hospital
                    last_child.child_birthdatereliability=profile_result.child_birthdatereliability
                    frappe.log_error(message=f"last_child: {last_child}", title="last_child")
                    last_child.save(ignore_permissions=True)
                    # ใช้ข้อมูลเด็กคนสุดท้าย (มีวันเกิดล่าสุด)
                    self.update_datahub_lookup(profile_result, last_child)
                except Exception as e:
                    frappe.log_error(message=f"Error sorting children by birthdate: {str(e)}", title="Child Sort Error")
                    # หากมีข้อผิดพลาดในการเรียงลำดับ ใช้ข้อมูลเด็กคนแรก
                    self.update_datahub_lookup(profile_result, child_profiles[0])
            else:
                self.update_datahub_lookup(profile_result, None)
              # อัพเดทสถานะ webhook
            webhook_doc.status = "Completed"
            webhook_doc.processed_at = datetime.now()
            webhook_doc.processing_result = frappe.as_json({
                "status": "success",
                "profile_id": profile_id
            })
            webhook_doc.save(ignore_permissions=True)
            
            return {"status": "success", "message": "Webhook data synced successfully", "profile_id": profile_id}
        except Exception as e:
            frappe.log_error(message=f"Webhook sync error: {str(e)}\n{frappe.get_traceback()}", title="Webhook Sync Error")
            
            # อัพเดทสถานะ webhook เป็น error
            try:
                webhook_doc.status = "Failed"
                webhook_doc.processed_at = datetime.now()
                webhook_doc.error_message = frappe.as_json({
                    "status": "error",
                    "message": str(e)
                })
                webhook_doc.save(ignore_permissions=True)
            except:
                pass
                
            raise e
    
    def create_sync_log(self, sync_type, raw_data, status="Pending"):
        """สร้างบันทึกการซิงค์"""
        try:
            log = frappe.get_doc({
                "doctype": self.sync_log_doctype,
                "sync_type": sync_type,
                "sync_date": datetime.now(),
                "status": status,
                "raw_data": frappe.as_json(raw_data) if isinstance(raw_data, dict) else raw_data
            })
            log.insert(ignore_permissions=True)
            return log.name
        except Exception as e:
            frappe.log_error(message=f"Error creating sync log: {str(e)}", title="Sync Log Error")
            return None 