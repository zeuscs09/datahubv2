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
from ...lib.ic360.client import IC360Client

class IC360Processor:
    def __init__(self, parent_processor):
        self.parent = parent_processor
        self.client = IC360Client()
    
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
            
            # เชื่อมต่อ IC360 database
            if not self.client.connect():
                return {"status": "error", "message": "Failed to connect to IC360 database"}
                
            # ตรวจสอบว่ามีโปรไฟล์อยู่แล้วหรือไม่
            check_query = "SELECT contact_id FROM ks_contact WHERE contact_id = %(contact_id)s"
            check_params = {"contact_id": contact_data.get("contact_id")}
            check_result = self.client.execute_query(check_query, check_params)
            
            if check_result and len(check_result) > 0:
                # อัพเดทโปรไฟล์ที่มีอยู่แล้ว
                update_query = """
                    UPDATE ks_contact 
                    SET first_name = %(first_name)s,
                        last_name = %(last_name)s,
                        gender = %(gender)s,
                        birth_date = %(birth_date)s,
                        contact_source = %(contact_source)s,
                        last_upd_dt = NOW()
                    WHERE contact_id = %(contact_id)s
                """
                self.client.execute_query(update_query, contact_data)
            else:
                # เพิ่มโปรไฟล์ใหม่
                insert_query = """
                    INSERT INTO ks_contact (
                        contact_id, first_name, last_name, gender,
                        birth_date, contact_source, create_dt, last_upd_dt
                    ) VALUES (
                        %(contact_id)s, %(first_name)s, %(last_name)s, %(gender)s,
                        %(birth_date)s, %(contact_source)s, NOW(), NOW()
                    )
                """
                self.client.execute_query(insert_query, contact_data)
            
            # อัพเดทข้อมูล Line
            if line_info_data.get("line_mid"):
                check_line_query = "SELECT contact_id FROM ks_contact_channel_lineinfo WHERE contact_id = %(contact_id)s"
                check_line_params = {"contact_id": line_info_data.get("contact_id")}
                check_line_result = self.client.execute_query(check_line_query, check_line_params)
                
                if check_line_result and len(check_line_result) > 0:
                    # อัพเดท Line ที่มีอยู่แล้ว
                    update_line_query = """
                        UPDATE ks_contact_channel_lineinfo 
                        SET line_mid = %(line_mid)s,
                            last_upd_dt = NOW()
                        WHERE contact_id = %(contact_id)s
                    """
                    self.client.execute_query(update_line_query, line_info_data)
                else:
                    # เพิ่ม Line ใหม่
                    insert_line_query = """
                        INSERT INTO ks_contact_channel_lineinfo (
                            contact_id, line_mid, create_dt, last_upd_dt
                        ) VALUES (
                            %(contact_id)s, %(line_mid)s, NOW(), NOW()
                        )
                    """
                    self.client.execute_query(insert_line_query, line_info_data)
            
            # อัพเดทข้อมูลอีเมล
            if email_data.get("channel_info"):
                check_email_query = """
                    SELECT contact_id 
                    FROM ks_contact_channel_dtl 
                    WHERE contact_id = %(contact_id)s
                    AND channel_type = 'PE'
                """
                check_email_params = {"contact_id": email_data.get("contact_id")}
                check_email_result = self.client.execute_query(check_email_query, check_email_params)
                
                if check_email_result and len(check_email_result) > 0:
                    # อัพเดทอีเมลที่มีอยู่แล้ว
                    update_email_query = """
                        UPDATE ks_contact_channel_dtl 
                        SET channel_info = %(channel_info)s,
                            is_primary = 1,
                            last_upd_dt = NOW()
                        WHERE contact_id = %(contact_id)s
                        AND channel_type = 'PE'
                    """
                    self.client.execute_query(update_email_query, email_data)
                else:
                    # เพิ่มอีเมลใหม่
                    insert_email_query = """
                        INSERT INTO ks_contact_channel_dtl (
                            contact_id, channel_type, channel_info,
                            create_dt, last_upd_dt, addr_seq_no, seq_no, is_primary
                        ) VALUES (
                            %(contact_id)s, 'PE', %(channel_info)s,
                            NOW(), NOW(), 0, 2, 1
                        )
                    """
                    self.client.execute_query(insert_email_query, email_data)
            
            # อัพเดทข้อมูลโทรศัพท์
            if mobile_data.get("channel_info"):
                check_mobile_query = """
                    SELECT contact_id 
                    FROM ks_contact_channel_dtl 
                    WHERE contact_id = %(contact_id)s
                    AND channel_type = 'M'
                """
                check_mobile_params = {"contact_id": mobile_data.get("contact_id")}
                check_mobile_result = self.client.execute_query(check_mobile_query, check_mobile_params)
                
                if check_mobile_result and len(check_mobile_result) > 0:
                    # อัพเดทโทรศัพท์ที่มีอยู่แล้ว
                    update_mobile_query = """
                        UPDATE ks_contact_channel_dtl 
                        SET channel_info = %(channel_info)s,
                            is_primary = 1,
                            last_upd_dt = NOW()
                        WHERE contact_id = %(contact_id)s
                        AND channel_type = 'M'
                    """
                    self.client.execute_query(update_mobile_query, mobile_data)
                else:
                    # เพิ่มโทรศัพท์ใหม่
                    insert_mobile_query = """
                        INSERT INTO ks_contact_channel_dtl (
                            contact_id, channel_type, channel_info,
                            create_dt, last_upd_dt, addr_seq_no, seq_no, is_primary
                        ) VALUES (
                            %(contact_id)s, 'M', %(channel_info)s,
                            NOW(), NOW(), 0, 1, 1
                        )
                    """
                    self.client.execute_query(insert_mobile_query, mobile_data)
            
            # อัพเดทข้อมูล nl_ks_contact
            check_nl_query = "SELECT contact_id FROM nl_ks_contact WHERE contact_id = %(contact_id)s"
            check_nl_params = {"contact_id": nl_ks_contact_data.get("contact_id")}
            check_nl_result = self.client.execute_query(check_nl_query, check_nl_params)
            
            if check_nl_result and len(check_nl_result) > 0:
                # อัพเดท nl_ks_contact ที่มีอยู่แล้ว
                update_nl_query = """
                    UPDATE nl_ks_contact 
                    SET flag_complete = %(flag_complete)s,
                        register_date = %(register_date)s,
                        agent_referral_code = %(agent_referral_code)s,
                        sourceid = %(sourceid)s,
                        last_upd_dt = NOW()
                    WHERE contact_id = %(contact_id)s
                """
                self.client.execute_query(update_nl_query, nl_ks_contact_data)
            else:
                # เพิ่ม nl_ks_contact ใหม่
                insert_nl_query = """
                    INSERT INTO nl_ks_contact (
                        contact_id, flag_complete, register_date,
                        agent_referral_code, sourceid, create_dt, last_upd_dt
                    ) VALUES (
                        %(contact_id)s, %(flag_complete)s, %(register_date)s,
                        %(agent_referral_code)s, %(sourceid)s, NOW(), NOW()
                    )
                """
                self.client.execute_query(insert_nl_query, nl_ks_contact_data)
            
            # อัพเดทข้อมูลที่อยู่
            if address_data.get("address_type"):
                check_addr_query = """
                    SELECT contact_id 
                    FROM ks_contact_addr_dtl 
                    WHERE contact_id = %(contact_id)s
                    AND address_type = %(address_type)s
                """
                check_addr_params = {"contact_id": address_data.get("contact_id"), "address_type": address_data.get("address_type")}
                check_addr_result = self.client.execute_query(check_addr_query, check_addr_params)
                
                if check_addr_result and len(check_addr_result) > 0:
                    # อัพเดทที่อยู่ที่มีอยู่แล้ว
                    update_addr_query = """
                        UPDATE ks_contact_addr_dtl 
                        SET addr_1 = %(addr_1)s,
                            sub_district = %(sub_district)s,
                            city = %(city)s,
                            state_code = %(state_code)s,
                            country_code = %(country_code)s,
                            last_upd_dt = NOW()
                        WHERE contact_id = %(contact_id)s
                        AND address_type = %(address_type)s
                    """
                    self.client.execute_query(update_addr_query, address_data)
                else:
                    # เพิ่มที่อยู่ใหม่
                    insert_addr_query = """
                        INSERT INTO ks_contact_addr_dtl (
                            contact_id, address_type, addr_1,
                            sub_district, city, state_code, country_code,
                            create_dt, last_upd_dt
                        ) VALUES (
                            %(contact_id)s, %(address_type)s, %(addr_1)s,
                            %(sub_district)s, %(city)s, %(state_code)s, %(country_code)s,
                            NOW(), NOW()
                        )
                    """
                    self.client.execute_query(insert_addr_query, address_data)
                
            result = {"status": "success", "message": "IC360 profile updated successfully"}
                
        except Exception as e:
            frappe.log_error(message=f"IC360 profile update error: {str(e)}", title="IC360 Profile Update Error")
            result = {"status": "error", "message": str(e)}
            
        finally:
            # ปิดการเชื่อมต่อ
            self.client.disconnect()
                
        return result
            
    def update_child(self, child_data):
        """อัพเดทข้อมูลเด็กใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_child_db_update(child_data):
                return {"status": "error", "message": "Invalid child data for IC360 update"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            child_ic360_data = transform_child_for_ic360(child_data)
            child_moreinfo_data = transform_child_moreinfo_for_ic360(child_data)
            
            # เชื่อมต่อ IC360 database
            if not self.client.connect():
                return {"status": "error", "message": "Failed to connect to IC360 database"}
                
            # ตรวจสอบว่ามีข้อมูลเด็กอยู่แล้วหรือไม่
            check_query = "SELECT cusid FROM nl_customer WHERE cusid = %(cusid)s"
            check_params = {"cusid": child_ic360_data.get("cusid")}
            check_result = self.client.execute_query(check_query, check_params)
            
            if check_result and len(check_result) > 0:
                # อัพเดทข้อมูลเด็กที่มีอยู่แล้ว
                update_query = """
                    UPDATE nl_customer 
                    SET motherid = %(motherid)s,
                        fname = %(fname)s,
                        lname = %(lname)s,
                        nname = %(nname)s,
                        gender = %(gender)s,
                        birthdate = %(birthdate)s,
                        reasonid = %(reasonid)s,
                        reason = %(reason)s,
                        remark = %(remark)s,
                        signature = %(signature)s,
                        updateid = '0',
                        updatedate = NOW(),
                        flag_complete = %(flag_complete)s,
                        flag_active = %(flag_active)s,
                        firstpro = %(firstpro)s,
                        firstformula = %(firstformula)s,
                        lastpro = %(lastpro)s,
                        lastformula = %(lastformula)s
                    WHERE cusid = %(cusid)s
                """
                self.client.execute_query(update_query, child_ic360_data)
            else:
                # เพิ่มข้อมูลเด็กใหม่
                insert_query = """
                    INSERT INTO nl_customer (
                        cusid, motherid, fname, lname, nname,
                        gender, birthdate, reasonid, reason, remark,
                        signature, createid, createdate, updateid, updatedate,
                        flag_complete, flag_active, firstpro, firstformula,
                        lastpro, lastformula, receivedate
                    ) VALUES (
                        %(cusid)s, %(motherid)s, %(fname)s, %(lname)s, %(nname)s,
                        %(gender)s, %(birthdate)s, %(reasonid)s, %(reason)s, %(remark)s,
                        %(signature)s, '0', NOW(), '0', NOW(),
                        %(flag_complete)s, %(flag_active)s, %(firstpro)s, %(firstformula)s,
                        %(lastpro)s, %(lastformula)s, %(receivedate)s
                    )
                """
                self.client.execute_query(insert_query, child_ic360_data)
            
            # อัพเดทข้อมูลเพิ่มเติมของเด็ก
            check_moreinfo_query = "SELECT cusid FROM nl_customer_moreinfo WHERE cusid = %(cusid)s"
            check_moreinfo_params = {"cusid": child_moreinfo_data.get("cusid")}
            check_moreinfo_result = self.client.execute_query(check_moreinfo_query, check_moreinfo_params)
            
            if check_moreinfo_result and len(check_moreinfo_result) > 0:
                # อัพเดทข้อมูลเพิ่มเติมที่มีอยู่แล้ว
                update_moreinfo_query = """
                    UPDATE nl_customer_moreinfo 
                    SET motherid = %(motherid)s,
                        born_place_id = %(born_place_id)s,
                        born_place_type = %(born_place_type)s,
                        birth_plan = %(birth_plan)s,
                        mother_prod_id = %(mother_prod_id)s,
                        current_mother_prod_id = %(current_mother_prod_id)s,
                        pc_code = %(pc_code)s,
                        mother_stage = %(mother_stage)s
                    WHERE cusid = %(cusid)s
                """
                self.client.execute_query(update_moreinfo_query, child_moreinfo_data)
            else:
                # เพิ่มข้อมูลเพิ่มเติมใหม่
                insert_moreinfo_query = """
                    INSERT INTO nl_customer_moreinfo (
                        cusid, motherid, born_place_id, born_place_type,
                        birth_plan, mother_prod_id, current_mother_prod_id,
                        pc_code, mother_stage
                    ) VALUES (
                        %(cusid)s, %(motherid)s, %(born_place_id)s, %(born_place_type)s,
                        %(birth_plan)s, %(mother_prod_id)s, %(current_mother_prod_id)s,
                        %(pc_code)s, %(mother_stage)s
                    )
                """
                self.client.execute_query(insert_moreinfo_query, child_moreinfo_data)
                
            result = {"status": "success", "message": "IC360 child updated successfully"}
                
        except Exception as e:
            frappe.log_error(message=f"IC360 child update error: {str(e)}", title="IC360 Child Update Error")
            result = {"status": "error", "message": str(e)}
            
        finally:
            # ปิดการเชื่อมต่อ
            self.client.disconnect()
                
        return result
            
    def update_consent(self, consent_data):
        """อัพเดทข้อมูลความยินยอมใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_consent_db_update(consent_data):
                return {"status": "error", "message": "Invalid consent data for IC360 update"}
            
            # เชื่อมต่อ IC360 database
            if not self.client.connect():
                return {"status": "error", "message": "Failed to connect to IC360 database"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            if consent_data.get("consent_type") == "MARKETING":
                # สร้างข้อมูลสำหรับความยินยอมทางการตลาด
                consent_ic360_data = transform_marketing_consent_for_ic360(consent_data)
                
                # ตรวจสอบว่ามีข้อมูลความยินยอมทางการตลาดอยู่แล้วหรือไม่
                check_query = """
                    SELECT contact_id 
                    FROM nl_marketing_consent 
                    WHERE contact_id = %(contact_id)s
                    AND channel = %(channel)s
                """
                check_params = {
                    "contact_id": consent_ic360_data.get("contact_id"),
                    "channel": consent_ic360_data.get("channel")
                }
                check_result = self.client.execute_query(check_query, check_params)
                
                if check_result and len(check_result) > 0:
                    # อัพเดทความยินยอมทางการตลาดที่มีอยู่แล้ว
                    update_query = """
                        UPDATE nl_marketing_consent 
                        SET consent_marketing = %(consent_marketing)s,
                            consent_marketing_dt = %(consent_marketing_dt)s,
                            consent_version = %(consent_version)s,
                            last_upd_dt = NOW()
                        WHERE contact_id = %(contact_id)s
                        AND channel = %(channel)s
                    """
                    self.client.execute_query(update_query, consent_ic360_data)
                else:
                    # เพิ่มความยินยอมทางการตลาดใหม่
                    insert_query = """
                        INSERT INTO nl_marketing_consent (
                            contact_id, channel, consent_marketing,
                            consent_marketing_dt, consent_version,
                            create_dt, last_upd_dt
                        ) VALUES (
                            %(contact_id)s, %(channel)s, %(consent_marketing)s,
                            %(consent_marketing_dt)s, %(consent_version)s,
                            NOW(), NOW()
                        )
                    """
                    self.client.execute_query(insert_query, consent_ic360_data)
                    
                result = {"status": "success", "message": "IC360 marketing consent updated successfully"}
                    
            elif consent_data.get("consent_type") == "PRIVACY":
                # สร้างข้อมูลสำหรับความยินยอมนโยบายความเป็นส่วนตัว
                consent_ic360_data = transform_primary_consent_for_ic360(consent_data)
            
                # ตรวจสอบว่ามีข้อมูลความยินยอมนโยบายความเป็นส่วนตัวอยู่แล้วหรือไม่
                check_query = """
                    SELECT contact_id 
                    FROM nl_primary_consent 
                    WHERE contact_id = %(contact_id)s
                    AND channel = %(channel)s
                """
                check_params = {
                    "contact_id": consent_ic360_data.get("contact_id"),
                    "channel": consent_ic360_data.get("channel")
                }
                check_result = self.client.execute_query(check_query, check_params)
                
                if check_result and len(check_result) > 0:
                    # อัพเดทความยินยอมนโยบายความเป็นส่วนตัวที่มีอยู่แล้ว
                    update_query = """
                        UPDATE nl_primary_consent 
                        SET consent_privacy_13y = %(consent_privacy_13y)s,
                            privacy_13y_dt = %(privacy_13y_dt)s,
                            consent_version = %(consent_version)s,
                            last_upd_dt = NOW()
                        WHERE contact_id = %(contact_id)s
                        AND channel = %(channel)s
                    """
                    self.client.execute_query(update_query, consent_ic360_data)
                else:
                    # เพิ่มความยินยอมนโยบายความเป็นส่วนตัวใหม่
                    insert_query = """
                        INSERT INTO nl_primary_consent (
                            contact_id, register_dt, channel,
                            consent_privacy_13y, privacy_13y_dt, consent_version,
                            create_dt, last_upd_dt
                        ) VALUES (
                            %(contact_id)s, NOW(), %(channel)s,
                            %(consent_privacy_13y)s, %(privacy_13y_dt)s, %(consent_version)s,
                            NOW(), NOW()
                        )
                    """
                    self.client.execute_query(insert_query, consent_ic360_data)
                    
                result = {"status": "success", "message": "IC360 privacy consent updated successfully"}
                
            else:
                result = {"status": "error", "message": "Unknown consent type"}
                
        except Exception as e:
            frappe.log_error(message=f"IC360 consent update error: {str(e)}", title="IC360 Consent Update Error")
            result = {"status": "error", "message": str(e)}
            
        finally:
            # ปิดการเชื่อมต่อ
            self.client.disconnect()
                
        return result
            
    def update_campaign(self, campaign_data):
        """อัพเดทข้อมูลแคมเปญใน IC360"""
        try:
            # ตรวจสอบความถูกต้องของข้อมูล
            if not validate_campaign_db_update(campaign_data):
                return {"status": "error", "message": "Invalid campaign data for IC360 update"}
            
            # แปลงข้อมูลสำหรับการอัพเดท
            campaign_ic360_data = transform_campaign_for_ic360(campaign_data)
            
            # เชื่อมต่อ IC360 database
            if not self.client.connect():
                return {"status": "error", "message": "Failed to connect to IC360 database"}
            
            # ตรวจสอบว่ามีข้อมูลแคมเปญอยู่แล้วหรือไม่
            check_query = """
                SELECT contact_id 
                FROM nl_contact_campaign 
                WHERE contact_id = %(contact_id)s
                AND application_code = %(application_code)s
                AND internal_id = %(internal_id)s
                AND internal_alternate_id = %(internal_alternate_id)s
            """
            check_params = {
                "contact_id": campaign_ic360_data.get("contact_id"),
                "application_code": campaign_ic360_data.get("application_code"),
                "internal_id": campaign_ic360_data.get("internal_id"),
                "internal_alternate_id": campaign_ic360_data.get("internal_alternate_id")
            }
            check_result = self.client.execute_query(check_query, check_params)
            
            if check_result and len(check_result) > 0:
                # อัพเดทข้อมูลแคมเปญที่มีอยู่แล้ว
                update_query = """
                    UPDATE nl_contact_campaign 
                    SET last_upd_dt = %(last_upd_dt)s
                    WHERE contact_id = %(contact_id)s
                    AND application_code = %(application_code)s
                    AND internal_id = %(internal_id)s
                    AND internal_alternate_id = %(internal_alternate_id)s
                """
                self.client.execute_query(update_query, campaign_ic360_data)
            else:
                # เพิ่มข้อมูลแคมเปญใหม่
                insert_query = """
                    INSERT INTO nl_contact_campaign (
                        contact_id, application_code, internal_id,
                        internal_alternate_id, create_dt, last_upd_dt
                    ) VALUES (
                        %(contact_id)s, %(application_code)s, %(internal_id)s,
                        %(internal_alternate_id)s, %(create_dt)s, %(last_upd_dt)s
                    )
                """
                self.client.execute_query(insert_query, campaign_ic360_data)
                
            result = {"status": "success", "message": "IC360 campaign updated successfully"}
                
        except Exception as e:
            frappe.log_error(message=f"IC360 campaign update error: {str(e)}", title="IC360 Campaign Update Error")
            result = {"status": "error", "message": str(e)}
            
        finally:
            # ปิดการเชื่อมต่อ
            self.client.disconnect()
                
        return result 