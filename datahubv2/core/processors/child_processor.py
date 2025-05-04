import frappe
from datetime import datetime, timedelta
from ..validator import validate_child_data
from ..transformer import transform_child_data
import uuid
from ..helper import Helper
class ChildProcessor:
    def __init__(self, parent_processor):
        self.parent = parent_processor
        self.child_doctype = parent_processor.child_doctype
    
    def process(self, data, parent_id):
        """ประมวลผลข้อมูลเด็ก"""
        # บันทึกข้อมูลดิบ
        frappe.log_error(message=f"Processing child data: {data}", title="DataHub Child Processing")
        
        # ตรวจสอบความถูกต้องของข้อมูล
        if not validate_child_data(data):
            return {"status": "error", "message": "Invalid child data"}
        
        # แปลงข้อมูลให้อยู่ในรูปแบบที่ต้องการ
        child_data = transform_child_data(data, parent_id)
        
        # ค้นหาเด็กที่มีวันเกิดใกล้เคียง
        existing_child = self.find_child(child_data)
        
        if existing_child:
            # อัพเดทข้อมูลที่มีอยู่
            child_result = self.update_child(existing_child, child_data)
        else:
            # สร้างข้อมูลเด็กใหม่
            child_result = self.create_child(child_data)
      
        return child_result
            
    def find_child(self, child_data):
        """ค้นหาเด็กที่มีวันเกิดใกล้เคียง (± 240 วัน)"""
        child = None
        
        # ถ้ามี cusid ให้ใช้ cusid ในการค้นหาก่อน
        if child_data.get("cusid"):
            try:
                children = frappe.get_list(
                    self.child_doctype,
                    filters={"cusid": child_data["cusid"]},
                    fields=["name"]
                )
                if children:
                    child = frappe.get_doc(self.child_doctype, children[0].name)
                    return child
            except Exception as e:
                frappe.log_error(message=f"Error finding child by cusid: {str(e)}", title="Child Find Error")
                
        # ถ้าไม่พบจาก cusid และมี birthdate ให้ค้นหาจากวันเกิด
        if not child and child_data.get("birthdate") and child_data.get("motherid"):
            try:
                birth_date = datetime.strptime(child_data["birthdate"], "%Y-%m-%d")
                min_date = (birth_date - timedelta(days=240)).strftime("%Y-%m-%d")
                max_date = (birth_date + timedelta(days=240)).strftime("%Y-%m-%d")
                
                children = frappe.get_list(
                    self.child_doctype,
                    filters=[
                        ["birthdate", ">=", min_date],
                        ["birthdate", "<=", max_date],
                        ["motherid", "=", child_data["motherid"]]
                    ],
                    fields=["name"]
                )
                
                if children:
                    child = frappe.get_doc(self.child_doctype, children[0].name)
            except Exception as e:
                frappe.log_error(message=f"Error finding child by birthdate: {str(e)}", title="Child Find Error")
                
        return child
        
    def update_child(self, existing_child, new_data):
        """อัพเดทข้อมูลเด็กที่มีอยู่"""
        try:
            for key, value in new_data.items():
                if value is not None and key != "cusid":  # ไม่อัพเดท cusid
                    setattr(existing_child, key, value)
                    
            existing_child.save(ignore_permissions=True)
            return existing_child
        except Exception as e:
            frappe.log_error(message=f"Child update error: {str(e)}", title="Child Update Error")
            raise
            
    def create_child(self, child_data):
        """สร้างข้อมูลเด็กใหม่"""
        try:
            # ตรวจสอบค่าที่จำเป็น
            if not child_data.get("cusid"):
                # สร้าง cusid ใหม่ (ควรมีการกำหนดรูปแบบตามต้องการ)
                child_data["cusid"] = Helper.generate_code(14)
            
            new_child = frappe.get_doc({
                "doctype": self.child_doctype,
                **child_data
            })
            new_child.insert(ignore_permissions=True)
            return new_child
        except Exception as e:
            frappe.log_error(message=f"Child creation error: {str(e)}", title="Child Creation Error")
            raise
    
    def get_last_child_id(self):
        """ดึงรหัสเด็กล่าสุดที่สร้าง"""
        try:
            children = frappe.get_list(
                self.child_doctype,
                fields=["name"],
                order_by="creation desc",
                limit=1
            )
            return children[0].name if children else None
        except Exception as e:
            frappe.log_error(message=f"Error getting last child ID: {str(e)}", title="Get Child ID Error")
            return None 