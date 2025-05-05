import frappe
import json
from datetime import datetime, timedelta
from .processors.profile_processor import ProfileProcessor
from .processors.child_processor import ChildProcessor
from .processors.campaign_processor import CampaignProcessor
from .processors.consent_processor import ConsentProcessor
from .processors.ic360_processor import IC360Processor
from ..utils.general import get_lookup_formula, get_lookup_data
from ..lib.ic360.client import IC360Client

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
            
            if area_info and isinstance(area_info, list) and len(area_info) > 0:
                area = area_info[0]
                if isinstance(area, dict):
                    main_profile.state_code = area.get("province_code")
                    main_profile.city = area.get("amphur_code")
                    main_profile.sub_district = area.get("district_code")
                    if area.get("zipcode") and not main_profile.postal_code:
                        main_profile.postal_code = area.get("zipcode")
       
        
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
                    lastpro = lookup_formula.value
                    prod_formula = lastpro.split("-")
                    child_profile.lastpro = prod_formula[0]
                    child_profile.lastformula = prod_formula[1]
                    formula_desc = get_lookup_formula("IC360", prod_formula[0])
                
                frappe.log_error(message=f"child_profile: {child_profile}", title="update_datahub_lookup:child_profile")
                child_profile.save(ignore_permissions=True)
        
    def update_sd_lookup(self, main_profile, child_profile):
        """ค้นหาข้อมูลจาก main profile และ child profile"""
        if main_profile:
            main_profile.data_source_code = get_lookup_data("IC360", "DataSourceCode", main_profile.sourceid)
            main_profile.gender_sd = get_lookup_data("IC360", "GENDER", main_profile.gender)
            main_profile.save(ignore_permissions=True)
        
        if child_profile:
            child_profile.gg_child_delivery_type = get_lookup_data("IC360", "NL_BIRTH_PLAN", child_profile.birth_plan)
            child_profile.gg_hospital = get_lookup_data("IC360", "NL_ANC_PLACE", child_profile.born_place_type)
            child_profile.child_birthdatereliability = get_lookup_data("IC360", "NL_MOTHERSTAGE", child_profile.mother_stage)
       
            if child_profile.lastpro and child_profile.lastformula:
                lastpro_key = child_profile.lastpro + "-" + child_profile.lastformula
        child_profile.gg_milk_currently_consuming = get_lookup_formula("IC360", lastpro_key)
            
        child_profile.save(ignore_permissions=True)
    def sync_from_webhook(self, webhook_doc,sync_type="MANUAL"):
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
            
            self.sync_to_ic360(profile_id)
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
    
    def sync_to_ic360(self, profile_id=None, sync_type="MANUAL"):
        """ซิงค์ข้อมูลจาก DataHub ไปยัง IC360"""
        try:
            # บันทึก log สำหรับการเริ่มต้น sync
            log_id = self.create_sync_log(
                sync_type=sync_type,
                raw_data={"profile_id": profile_id, "sync_type": sync_type},
                status="Processing"
            )
            
            frappe.log_error(message=f"Starting IC360 sync for profile_id: {profile_id}, sync_type: {sync_type}", title="IC360 Sync Start")
            
            # ดึงข้อมูลโปรไฟล์จาก DataHub
            if profile_id:
                # ซิงค์เฉพาะโปรไฟล์ที่ระบุ
                profile_list = [frappe.get_doc(self.profile_doctype, profile_id)]
            else:
                # ดึงโปรไฟล์ทั้งหมดที่ยังไม่ได้ซิงค์หรือที่มีการอัพเดท
                # เงื่อนไขในการเลือกโปรไฟล์ต้องกำหนดเพิ่มเติม เช่น มีฟิลด์ is_synced หรือ last_synced_to_ic360
                profile_list = frappe.get_all(
                    self.profile_doctype,
                    filters={"is_synced_to_ic360": 0},  # สมมติว่ามีฟิลด์นี้
                    fields=["name"],
                    limit=100  # จำกัดจำนวนโปรไฟล์ที่ซิงค์ในแต่ละครั้ง
                )
                profile_list = [frappe.get_doc(self.profile_doctype, p.name) for p in profile_list]
            
            results = []
            for profile in profile_list:
                try:
                    # อัพเดทข้อมูล lookup ก่อนส่งไปยัง IC360
                    self.update_sd_lookup(profile, None)
                    
                    # อัพเดทข้อมูลโปรไฟล์ไปยัง IC360
                    profile_result = self.update_ic360_profile(profile)
                    
                    # ดึงข้อมูลเด็กที่เกี่ยวข้อง
                    children = frappe.get_all(
                        self.child_doctype,
                        filters={"motherid": profile.name},
                        fields=["name"]
                    )
                    
                    child_results = []
                    for child in children:
                        child_doc = frappe.get_doc(self.child_doctype, child.name)
                        
                        # อัพเดทข้อมูล lookup สำหรับเด็ก
                        self.update_sd_lookup(profile, child_doc)
                        
                        # อัพเดทข้อมูลเด็กไปยัง IC360
                        child_result = self.update_ic360_child(child_doc)
                        child_results.append({
                            "child_id": child_doc.name,
                            "result": child_result
                        })
                    
                    # ดึงข้อมูลความยินยอม
                    consents = frappe.get_all(
                        self.consent_doctype,
                        filters={"contact_id": profile.name},
                        fields=["name"]
                    )
                    
                    consent_results = []
                    for consent in consents:
                        consent_doc = frappe.get_doc(self.consent_doctype, consent.name)
                        
                        # อัพเดทข้อมูลความยินยอมไปยัง IC360
                        consent_result = self.update_ic360_consent(consent_doc)
                        consent_results.append({
                            "consent_id": consent_doc.name,
                            "result": consent_result
                        })
                    
                    # ดึงข้อมูลแคมเปญ
                    campaigns = frappe.get_all(
                        self.campaign_doctype,
                        filters={"contact_id": profile.name},
                        fields=["name"]
                    )
                    
                    campaign_results = []
                    for campaign in campaigns:
                        campaign_doc = frappe.get_doc(self.campaign_doctype, campaign.name)
                        
                        # อัพเดทข้อมูลแคมเปญไปยัง IC360
                        campaign_result = self.update_ic360_campaign(campaign_doc)
                        campaign_results.append({
                            "campaign_id": campaign_doc.name,
                            "result": campaign_result
                        })
                    
                    # บันทึกผลการซิงค์
                    result = {
                        "profile_id": profile.name,
                        "profile_result": profile_result,
                        "child_results": child_results,
                        "consent_results": consent_results,
                        "campaign_results": campaign_results
                    }
                    
                    results.append(result)
                    
                    # อัพเดทสถานะการซิงค์ของโปรไฟล์
                    # profile.is_synced_to_ic360 = 1  # สมมติว่ามีฟิลด์นี้
                    # profile.last_synced_to_ic360 = datetime.now()
                    profile.save(ignore_permissions=True)
                    
                except Exception as e:
                    frappe.log_error(message=f"IC360 sync error for profile {profile.name}: {str(e)}", title="IC360 Sync Profile Error")
                    results.append({
                        "profile_id": profile.name,
                        "error": str(e)
                    })
            
            # อัพเดท sync log
            log_doc = frappe.get_doc(self.sync_log_doctype, log_id)
            log_doc.status = "Completed"
            log_doc.processed_records = len(results)
            log_doc.total_records = len(profile_list)
            log_doc.processing_result = frappe.as_json(results)
            log_doc.save(ignore_permissions=True)
            
            return {
                "status": "success", 
                "message": f"Synced {len(results)} profiles to IC360", 
                "results": results
            }
            
        except Exception as e:
            frappe.log_error(message=f"IC360 sync error: {str(e)}\n{frappe.get_traceback()}", title="IC360 Sync Error")
            
            # อัพเดท sync log
            if log_id:
                try:
                    log_doc = frappe.get_doc(self.sync_log_doctype, log_id)
                    log_doc.status = "Failed"
                    log_doc.error_log = str(e)
                    log_doc.save(ignore_permissions=True)
                except:
                    pass
            
            return {"status": "error", "message": str(e)}
    
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