import frappe
import uuid
from datetime import datetime
from ..validator import validate_profile_data
from ..transformer import transform_profile_data
from ..helper import Helper

class ProfileProcessor:
    def __init__(self, parent_processor):
        self.parent = parent_processor
        self.profile_doctype = parent_processor.profile_doctype
    
    def process(self, data):
        """ประมวลผลข้อมูลโปรไฟล์"""
        # บันทึกข้อมูลดิบ
        frappe.log_error(message=f"Processing profile data: {data}", title="DataHub Profile Processing")
        
        # ตรวจสอบความถูกต้องของข้อมูล
        if not validate_profile_data(data):
            return {"status": "error", "message": "Invalid profile data"}
            
        # แปลงข้อมูลให้อยู่ในรูปแบบที่ต้องการ
        profile_data = transform_profile_data(data)
        
        # ค้นหาโปรไฟล์ที่มีอยู่
        existing_profile = self.find_profile(profile_data)
        
        if existing_profile:
            # อัพเดทข้อมูลที่มีอยู่
            profile_result = self.update_profile(existing_profile, profile_data)
           
        else:
            # สร้างโปรไฟล์ใหม่
            profile_id = Helper.generate_code(14)
            profile_data["contact_id"] = profile_id
            profile_data["contact_type"] = "09"
            profile_result = self.create_profile(profile_data)
            
        return  profile_result
            
    def find_profile(self, profile_data):
        """ค้นหาโปรไฟล์ที่มีอยู่
        1. ค้นหาด้วย uid ก่อน
        2. ถ้าไม่เจอด้วย uid ให้ค้นหาด้วยเบอร์โทร
        """
        profile = None
        
        # ค้นหาด้วย uid ก่อน
        if profile_data.get("uid"):
            try:
                profiles = frappe.get_list(
                    self.profile_doctype,
                    filters={"uid": profile_data["uid"]},
                    fields=["name"]
                )
                if profiles:
                    profile = frappe.get_doc(self.profile_doctype, profiles[0].name)
            except Exception as e:
                frappe.log_error(message=f"Error finding profile by uid: {str(e)}", title="Profile Find Error")
                raise
                
        # ถ้าไม่เจอด้วย uid ให้ค้นหาด้วยเบอร์โทร
        if not profile and profile_data.get("phone"):
            try:
                phone = profile_data["phone"]
                phone_variants = [phone]  # เก็บรูปแบบต่างๆ ของเบอร์โทร
                
                # สร้างรูปแบบเบอร์โทรที่แตกต่างกัน
                if phone.startswith("+66"):
                    # +66812345678 -> 0812345678
                    phone_variants.append("0" + phone[3:])
                elif phone.startswith("0"):
                    # 0812345678 -> +66812345678
                    phone_variants.append("+66" + phone[1:])
                
                # ค้นหาโปรไฟล์จากรูปแบบเบอร์โทรทั้งหมด
                profiles = frappe.get_list(
                    self.profile_doctype,
                    filters={"phone": ["in", phone_variants]},
                    fields=["name"]
                )
                if profiles:
                    profile = frappe.get_doc(self.profile_doctype, profiles[0].name)
            except Exception as e:
                frappe.log_error(message=f"Error finding profile by phone: {str(e)}", title="Profile Find Error")
                raise
                
        return profile
        
    def update_profile(self, existing_profile, new_data):
        """อัพเดทข้อมูลโปรไฟล์ที่มีอยู่"""
        try:
            for key, value in new_data.items():
                if value is not None and key != "uid":  # ไม่อัพเดท uid
                    setattr(existing_profile, key, value)
                    
            existing_profile.save(ignore_permissions=True)
            return existing_profile
        except Exception as e:
            frappe.log_error(message=f"Profile update error: {str(e)}", title="Profile Update Error")
            raise
            
    def create_profile(self, profile_data):
        """สร้างโปรไฟล์ใหม่"""
        try:
            # ตรวจสอบค่าที่จำเป็น
            if not profile_data.get("uid"):
                profile_data["uid"] = str(uuid.uuid4())
            
            new_profile = frappe.get_doc({
                "doctype": self.profile_doctype,
                **profile_data
            })
            new_profile.insert(ignore_permissions=True)
            
            # บันทึก log สำหรับการดีบัก
            frappe.log_error(message=f"Profile created with ID: {new_profile.name}", title="Profile Creation")
            
            return new_profile
        except Exception as e:
            frappe.log_error(message=f"Profile creation error: {str(e)}", title="Profile Creation Error")
            raise
    
    def get_last_profile_id(self):
        """ดึงรหัสโปรไฟล์ล่าสุดที่สร้าง"""
        try:
            profiles = frappe.get_list(
                self.profile_doctype,
                fields=["name"],
                order_by="creation desc",
                limit=1
            )
            return profiles[0].name if profiles else None
        except Exception as e:
            frappe.log_error(message=f"Error getting last profile ID: {str(e)}", title="Get Profile ID Error")
            return None 