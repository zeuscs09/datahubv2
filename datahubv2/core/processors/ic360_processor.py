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
from ...core.lookup import update_sd_lookup

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
                        last_upd_dt = NOW(),
                        is_active = %(is_active)s,
                        income = %(income)s,
                        contact_type = %(contact_type)s
                    WHERE contact_id = %(contact_id)s
                """
                self.client.execute_query(update_query, contact_data)
            else:
                # เพิ่มโปรไฟล์ใหม่
                insert_query = """
                    INSERT INTO ks_contact (
                        contact_id, first_name, last_name, gender,
                        birth_date, contact_source, create_dt, last_upd_dt,is_active,income,contact_type
                    ) VALUES (
                        %(contact_id)s, %(first_name)s, %(last_name)s, %(gender)s,
                        %(birth_date)s, %(contact_source)s, NOW(), NOW(),%(is_active)s,%(income)s,%(contact_type)s
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
                            postal_code = %(postal_code)s,
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
                            create_dt, last_upd_dt,addr_seq_no,postal_code  
                        ) VALUES (
                            %(contact_id)s, %(address_type)s, %(addr_1)s,
                            %(sub_district)s, %(city)s, %(state_code)s, %(country_code)s,
                            NOW(), NOW(),1,%(postal_code)s
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
            main_profile = frappe.get_doc("ETL Main Profile", child_data.get("motherid"))
            child_moreinfo_data["sourceid"] = main_profile.get("sourceid")
            child_ic360_data["sourceid"] = main_profile.get("sourceid")
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
                        lastformula = %(lastformula)s,
                        sourceid = %(sourceid)s,
                        receivedate = %(receivedate)s
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
                        lastpro, lastformula, receivedate,sourceid,receivedate
                    ) VALUES (
                        %(cusid)s, %(motherid)s, %(fname)s, %(lname)s, %(nname)s,
                        %(gender)s, %(birthdate)s, %(reasonid)s, %(reason)s, %(remark)s,
                        %(signature)s, '0', NOW(), '0', NOW(),
                        %(flag_complete)s, %(flag_active)s, %(firstpro)s, %(firstformula)s,
                        %(lastpro)s, %(lastformula)s, %(receivedate)s,%(sourceid)s,%(receivedate)s
                    )
                """
                self.client.execute_query(insert_query, child_ic360_data)
            reasonid_update =f"""
            UPDATE nl_customer cus
            SET reasonid = nr.reasonid
            FROM nl_reason nr
            WHERE cus.reason = nr.reasonth
            AND cus.motherid = %(motherid)s;
                        """
            self.client.execute_query(reasonid_update, child_ic360_data)
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
                        mother_stage = %(mother_stage)s,
                        sourceid = %(sourceid)s
                    WHERE cusid = %(cusid)s
                """
                self.client.execute_query(update_moreinfo_query, child_moreinfo_data)
            else:
                # เพิ่มข้อมูลเพิ่มเติมใหม่
                insert_moreinfo_query = """
                    INSERT INTO nl_customer_moreinfo (
                        cusid, motherid, born_place_id, born_place_type,
                        birth_plan, mother_prod_id, current_mother_prod_id,
                        pc_code, mother_stage,sourceid
                    ) VALUES (
                        %(cusid)s, %(motherid)s, %(born_place_id)s, %(born_place_type)s,
                        %(birth_plan)s, %(mother_prod_id)s, %(current_mother_prod_id)s,
                        %(pc_code)s, %(mother_stage)s,%(sourceid)s
                    )
                """
                self.client.execute_query(insert_moreinfo_query, child_moreinfo_data)
                
            result = {"status": "success", "message": "IC360 child updated successfully"}
                
        except Exception as e:
            frappe.log_error(message=f"IC360 child update error: {str(e)}", title="IC360 Child Update Error")
            raise e
            
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
            if not campaign_ic360_data.get("internal_alternate_id"):
                campaign_ic360_data["internal_alternate_id"] = ""
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

    def sync_from_ic360(self, contact_id):
        """ซิงค์ข้อมูลจาก IC360 มาเก็บใน DataHub"""
        try:
            # เชื่อมต่อ IC360 database
            if not self.client.connect():
                return {"status": "error", "message": "Failed to connect to IC360 database"}
            
            # บันทึก log สำหรับการเริ่มต้น sync
            log_id = self.parent.create_sync_log(
                sync_type="INBOUND",
                raw_data={"contact_id": contact_id},
                status="Processing"
            )
            
            frappe.log_error(message=f"Starting IC360 sync for contact_id: {contact_id}", title="IC360 Sync Start")
            
            # 1. ดึงข้อมูลโปรไฟล์จาก IC360
            profile_query = """
                SELECT 
                    c.contact_id,
                    c.first_name,
                    c.last_name,
                    c.contact_no,
                    c.is_active,
                    c.gender,
                    c.birth_date,
                    c.contact_type,
                    c.create_user_id,
                    c.create_company_id,
                    c.create_group_id,
                    c.create_dt,
                    c.last_upd_user_id,
                    c.last_upd_company_id,
                    c.last_upd_group_id,
                    c.last_upd_dt,
                    c.id_card_no,
                    c.contact_source,
                    COALESCE(NULLIF(CASE 
                        WHEN c.income ~ '^[0-9]+\.?[0-9]*$' THEN c.income 
                        ELSE '0' 
                    END, ''), '0')::numeric as income,
                    ca.addr_1,
                    ca.sub_district,
                    ma.district_name as sub_district_name,
                    ca.city,
                    ma.amphur_name,
                    ca.state_code,
                    ma.province_name,
                    ma.zipcode postal_code,
                    ca.country_code,
                    cl.line_mid,
                    ce.channel_info as email,
                    cm.channel_info as mobile,
                    nkc.sourceid,
                    nkc.flag_complete,
                    nkc.register_date,
                    nkc.mother_stage,
                    nkc.agent_referral_code,
                    coalesce(uuid.uuid, '') as uid
                FROM 
                    ks_contact c
                LEFT JOIN 
                    ks_contact_addr_dtl ca ON c.contact_id = ca.contact_id 
                    AND ca.address_type = 'HOME'
                LEFT JOIN 
                    ks_contact_channel_lineinfo cl ON c.contact_id = cl.contact_id
                LEFT JOIN 
                    ks_contact_channel_dtl ce ON c.contact_id = ce.contact_id 
                    AND ce.channel_type = 'PE' AND ce.is_primary=1
                LEFT JOIN 
                    ks_contact_channel_dtl cm ON c.contact_id = cm.contact_id 
                    AND cm.channel_type = 'M' AND cm.is_primary=1
                LEFT JOIN (
                    SELECT
                        province_code,
                        province_name,
                        amphur_code,
                        amphur_name,
                        district_code,
                        district_name,
                        zipcode 
                    FROM
                        ks_province kp
                ) ma ON ca.sub_district = ma.district_code 
                    AND ca.city = ma.amphur_code 
                    AND ca.state_code = ma.province_code
                LEFT JOIN 
                    nl_ks_contact nkc ON c.contact_id = nkc.contact_id 
                LEFT JOIN 
                    nl_query_smartdata_project_uuid_migration uuid ON c.contact_id = uuid.contact_id
                WHERE 
                    c.contact_id = %(contact_id)s
            """
            
            profile_result = self.client.execute_query(profile_query, {"contact_id": contact_id})
            
            if not profile_result:
                # อัพเดท sync log
                if log_id:
                    log_doc = frappe.get_doc(self.parent.sync_log_doctype, log_id)
                    log_doc.status = "Failed"
                    log_doc.error_log = "Contact not found in IC360"
                    log_doc.save(ignore_permissions=True)
                return {"status": "error", "message": "Contact not found in IC360"}
            
            profile_data = profile_result[0]
            
            # แปลงข้อมูลสำหรับ Main Profile
            main_profile_data = {
                "contact_id": profile_data.get("contact_id"),
                "uid": profile_data.get("uid"),
                "first_name": profile_data.get("first_name"),
                "last_name": profile_data.get("last_name"),
                "gender": profile_data.get("gender"),
                "gender_sd": profile_data.get("gender"),
                "birth_date": profile_data.get("birth_date"),
                "phone": profile_data.get("mobile"),
                "email": profile_data.get("email"),
                "line_mid": profile_data.get("line_mid"),
                "address": profile_data.get("addr_1"),
                "state_code": profile_data.get("state_code"),
                "province_name": profile_data.get("province_name"),
                "city": profile_data.get("city"),
                "amphur_name": profile_data.get("amphur_name"),
                "sub_district": profile_data.get("sub_district"),
                "sub_district_name": profile_data.get("sub_district_name"),
                "postal_code": profile_data.get("postal_code"),
                "income": profile_data.get("income"),
                "contact_source": profile_data.get("contact_source"),
                "sourceid": profile_data.get("sourceid"),
                "data_source_code": profile_data.get("sourceid"),
                "nestle_agent_referral_code": profile_data.get("agent_referral_code"),
                "date_registration": profile_data.get("register_date"),
                "last_updated": profile_data.get("last_upd_dt")
            }
            
            # ค้นหา profile ใน DataHub
            existing_profile = frappe.get_all(
                "ETL Main Profile",
                filters={"contact_id": contact_id},
                fields=["name"]
            )
            
            if existing_profile:
                # อัพเดท profile ที่มีอยู่
                doc = frappe.get_doc("ETL Main Profile", existing_profile[0].name)
                doc.update(main_profile_data)
                doc.save(ignore_permissions=True)
                profile_id = doc.name
            else:
                # สร้าง profile ใหม่
                doc = frappe.get_doc({
                    "doctype": "ETL Main Profile",
                    **main_profile_data
                })
                doc.insert(ignore_permissions=True)
                profile_id = doc.name
            
            # 2. ดึงข้อมูลเด็กจาก IC360
            child_query = """
                SELECT 
                    c.cusid,
                    c.motherid,
                    c.fname,
                    c.lname, 
                    c.nname,
                    c.gender,
                    c.birthdate,
                    c.reasonid,
                    rs.reasonth reasonidtext,
                    c.reason,
                    c.remark,
                    c.firstpro,
                    c.firstformula,
                    c.lastpro,
                    c.lastformula,
                    c.createid,
                    c.createdate,
                    c.updateid,
                    c.updatedate,
                    c.flag_complete,
                    c.flag_active,
                    c.receivedate,
                    c.signature,
                    m.born_place_id,
                    m.born_place_type,
                    m.birth_plan,
                    m.mother_prod_id,
                    m.current_mother_prod_id,
                    m.pc_code,
                    m.mother_stage
                FROM nl_customer c
                LEFT JOIN nl_customer_moreinfo m ON c.cusid = m.cusid 
                LEFT JOIN nl_reason rs on c.reasonid = rs.reasonid 
                WHERE c.motherid = %(contact_id)s
                AND c.flag_active = '1'
            """
            
            child_result = self.client.execute_query(child_query, {"contact_id": contact_id})
            
            # สำหรับเก็บข้อมูลเด็กคนสุดท้าย เพื่ออัพเดท main profile
            latest_child_data = None
            child_ids = []
            
            # ประมวลผลข้อมูลเด็ก
            for child_data in child_result:
                child_mapping = {
                    "cusid": child_data.get("cusid"),
                    "motherid": profile_id,  # ใช้ document ID ของ ETL Main Profile
                    "fname": child_data.get("fname"),
                    "lname": child_data.get("lname"),
                    "nname": child_data.get("nname"),
                    "gender": child_data.get("gender"),
                    "birthdate": child_data.get("birthdate"),
                    "child_type": child_data.get("child_type"),
                    "child_status": child_data.get("child_status"),
                    "child_stage": child_data.get("child_stage"),
                    "born_place_id": child_data.get("born_place_id"),
                    "born_place_type": child_data.get("born_place_type"),
                    #"gg_hospital": child_data.get("born_place_type"),  # จะมีการแปลงค่าภายหลัง
                    "birth_plan": child_data.get("birth_plan"),
                    #"gg_child_delivery_type": child_data.get("birth_plan"),  # จะมีการแปลงค่าภายหลัง
                    "mother_prod_id": child_data.get("mother_prod_id"),
                    "current_mother_prod_id": child_data.get("current_mother_prod_id"),
                    "firstpro": child_data.get("firstpro"),
                    "firstformula": child_data.get("firstformula"),
                    "lastpro": child_data.get("lastpro"),
                    "lastformula": child_data.get("lastformula"),
                    #"gg_milk_currently_consuming": child_data.get("lastformula"),  # จะมีการแปลงค่าภายหลัง
                    "reasonid": child_data.get("reasonid"),
                    "reason": child_data.get("reason"),
                    "pc_code": child_data.get("pc_code"),
                    "mother_stage": child_data.get("mother_stage"),
                    #"child_birthdatereliability": child_data.get("mother_stage"),  # จะมีการแปลงค่าภายหลัง
                    "createid": child_data.get("createid"),
                    "createdate": child_data.get("createdate"),
                    "updateid": child_data.get("updateid"),
                    "updatedate": child_data.get("updatedate"),
                    "flag_complete": child_data.get("flag_complete"),
                    "flag_active": child_data.get("flag_active"),
                    "receivedate": child_data.get("receivedate"),
                    "signature": child_data.get("signature")
                }
                
                # ค้นหาเด็กที่มีอยู่แล้ว
                existing_child = frappe.get_all(
                    "ETL Child",
                    filters={"cusid": child_data.get("cusid")},
                    fields=["name"]
                )
                
                if existing_child:
                    # อัพเดทข้อมูลเด็กที่มีอยู่
                    child_doc = frappe.get_doc("ETL Child", existing_child[0].name)
                    child_doc.update(child_mapping)
                    child_doc.save(ignore_permissions=True)
                    child_ids.append(child_doc.name)
                else:
                    # สร้างข้อมูลเด็กใหม่
                    child_doc = frappe.get_doc({
                        "doctype": "ETL Child",
                        **child_mapping
                    })
                    child_doc.insert(ignore_permissions=True)
                    child_ids.append(child_doc.name)
                
                # เก็บข้อมูลเด็กคนล่าสุด
                if not latest_child_data or (child_data.get("updatedate") and (not latest_child_data.get("updatedate") or child_data.get("updatedate") > latest_child_data.get("updatedate"))):
                    latest_child_data = child_data
                    
            update_sd_lookup(doc,latest_child_data)
            
            # อัพเดท Main Profile ด้วยข้อมูลเด็กคนล่าสุด
            if latest_child_data:
                main_profile_update = {
                    "gg_hospital": latest_child_data.get("gg_hospital"),
                    "gg_child_delivery_type": latest_child_data.get("gg_child_delivery_type"),
                    "gg_milk_currently_consuming": latest_child_data.get("gg_milk_currently_consuming"),
                    "child_birthdatereliability": latest_child_data.get("child_birthdatereliability")
                }
                
                # อัพเดท lookup values ตามความเหมาะสม
                # self.parent.update_sd_lookup(doc, None)
                
                # อัพเดทข้อมูล main profile
                doc = frappe.get_doc("ETL Main Profile", profile_id)
                doc.update(main_profile_update)
                doc.save(ignore_permissions=True)
            
            # 3. ดึงข้อมูลแคมเปญจาก IC360
            campaign_query = """
                SELECT 
                    contact_id,
                    application_code,
                    internal_id,
                    internal_alternate_id,
                    create_dt,
                    last_upd_dt
                FROM nl_contact_campaign 
                WHERE contact_id = %(contact_id)s
            """
            
            campaign_result = self.client.execute_query(campaign_query, {"contact_id": contact_id})
            campaign_ids = []
            
            # ประมวลผลข้อมูลแคมเปญ
            for campaign_data in campaign_result:
                campaign_mapping = {
                    "contact_id": profile_id,  # ใช้ document ID ของ ETL Main Profile
                    "campaign_id": f"{campaign_data.get('application_code')}_{campaign_data.get('internal_id')}",
                    "application_code": campaign_data.get("application_code"),
                    "internal_id": campaign_data.get("internal_id"),
                    "internal_alternate_id": campaign_data.get("internal_alternate_id"),
                    "create_date": campaign_data.get("create_dt"),
                    "last_update_date": campaign_data.get("last_upd_dt")
                }
                
                # ค้นหาแคมเปญที่มีอยู่แล้ว
                existing_campaign = frappe.get_all(
                    "ETL Campaign",
                    filters={
                        "contact_id": profile_id,
                        "application_code": campaign_data.get("application_code"),
                        "internal_id": campaign_data.get("internal_id")
                    },
                    fields=["name"]
                )
                
                if existing_campaign:
                    # อัพเดทข้อมูลแคมเปญที่มีอยู่
                    campaign_doc = frappe.get_doc("ETL Campaign", existing_campaign[0].name)
                    campaign_doc.update(campaign_mapping)
                    campaign_doc.save(ignore_permissions=True)
                    campaign_ids.append(campaign_doc.name)
                else:
                    # สร้างข้อมูลแคมเปญใหม่
                    campaign_doc = frappe.get_doc({
                        "doctype": "ETL Campaign",
                        **campaign_mapping
                    })
                    campaign_doc.insert(ignore_permissions=True)
                    campaign_ids.append(campaign_doc.name)
            
            # 4. ดึงข้อมูลความยินยอมจาก IC360
            # 4.1 ความยินยอมนโยบายความเป็นส่วนตัว
            privacy_query = """
                SELECT 
                    contact_id,
                    register_dt,
                    channel,
                    consent_privacy_13y,
                    privacy_13y_dt,
                    consent_version,
                    create_dt,
                    last_upd_dt
                FROM nl_primary_consent 
                WHERE contact_id = %(contact_id)s
            """
            
            privacy_result = self.client.execute_query(privacy_query, {"contact_id": contact_id})
            consent_ids = []
            
            # ประมวลผลความยินยอมนโยบายความเป็นส่วนตัว
            for privacy_data in privacy_result:
                privacy_mapping = {
                    "contact_id": profile_id,  # ใช้ document ID ของ ETL Main Profile
                    "consent_type": "PRIVACY",
                    "consent_status": privacy_data.get("consent_privacy_13y"),
                    "consent_date": privacy_data.get("privacy_13y_dt"),
                    "consent_version": privacy_data.get("consent_version"),
                    "is_consented": privacy_data.get("consent_privacy_13y"),
                    "date_registration": privacy_data.get("register_dt"),
                    "last_updated": privacy_data.get("last_upd_dt")
                }
                
                # ค้นหาความยินยอมที่มีอยู่แล้ว
                existing_consent = frappe.get_all(
                    "ETL Consent",
                    filters={
                        "contact_id": profile_id,
                        "consent_type": "PRIVACY",
                        "consent_version": privacy_data.get("consent_version")
                    },
                    fields=["name"]
                )
                
                if existing_consent:
                    # อัพเดทข้อมูลความยินยอมที่มีอยู่
                    consent_doc = frappe.get_doc("ETL Consent", existing_consent[0].name)
                    consent_doc.update(privacy_mapping)
                    consent_doc.save(ignore_permissions=True)
                    consent_ids.append(consent_doc.name)
                else:
                    # สร้างข้อมูลความยินยอมใหม่
                    consent_doc = frappe.get_doc({
                        "doctype": "ETL Consent",
                        **privacy_mapping
                    })
                    consent_doc.insert(ignore_permissions=True)
                    consent_ids.append(consent_doc.name)
            
            # 4.2 ความยินยอมทางการตลาด
            marketing_query = """
                SELECT 
                    contact_id,
                    channel,
                    consent_marketing,
                    consent_marketing_dt,
                    consent_version,
                    create_dt,
                    last_upd_dt
                FROM nl_marketing_consent 
                WHERE contact_id = %(contact_id)s
            """
            
            marketing_result = self.client.execute_query(marketing_query, {"contact_id": contact_id})
            
            # ประมวลผลความยินยอมทางการตลาด
            for marketing_data in marketing_result:
                marketing_mapping = {
                    "contact_id": profile_id,  # ใช้ document ID ของ ETL Main Profile
                    "consent_type": "MARKETING",
                    "consent_status": marketing_data.get("consent_marketing"),
                    "consent_date": marketing_data.get("consent_marketing_dt"),
                    "consent_version": marketing_data.get("consent_version"),
                    "is_consented": marketing_data.get("consent_marketing"),
                    "marketing_subscribed_date": marketing_data.get("consent_marketing_dt"),
                    "marketing_subscribed_version": marketing_data.get("consent_version"),
                    "date_registration": marketing_data.get("create_dt"),
                    "last_updated": marketing_data.get("last_upd_dt")
                }
                
                # ค้นหาความยินยอมที่มีอยู่แล้ว
                existing_consent = frappe.get_all(
                    "ETL Consent",
                    filters={
                        "contact_id": profile_id,
                        "consent_type": "MARKETING",
                        "consent_version": marketing_data.get("consent_version")
                    },
                    fields=["name"]
                )
                
                if existing_consent:
                    # อัพเดทข้อมูลความยินยอมที่มีอยู่
                    consent_doc = frappe.get_doc("ETL Consent", existing_consent[0].name)
                    consent_doc.update(marketing_mapping)
                    consent_doc.save(ignore_permissions=True)
                    consent_ids.append(consent_doc.name)
                else:
                    # สร้างข้อมูลความยินยอมใหม่
                    consent_doc = frappe.get_doc({
                        "doctype": "ETL Consent",
                        **marketing_mapping
                    })
                    consent_doc.insert(ignore_permissions=True)
                    consent_ids.append(consent_doc.name)
            
            # ก่อนสร้าง JSON สำหรับ outbound
            # ดึงข้อมูล consent type MARKETING จาก ETL Consent
            marketing_consent = None
            marketing_consents = frappe.get_all(
                "ETL Consent",
                filters={
                    "contact_id": profile_id,
                    "consent_type": "MARKETING"
                },
                fields=["consent_status", "consent_date", "consent_version", "is_consented"],
                order_by="creation desc",
                limit=1
            )

            if marketing_consents:
                marketing_consent = marketing_consents[0]

            privacy_consent = None
            privacy_consents = frappe.get_all(
                "ETL Consent",
                filters={
                    "contact_id": profile_id,
                    "consent_type": "PRIVACY"
                },
                fields=["consent_status", "consent_date", "consent_version", "is_consented"],
                order_by="creation desc",
                limit=1
            )

            if privacy_consents:
                privacy_consent = privacy_consents[0]

            # 5. สร้าง JSON สำหรับ outbound
            outbound_data = {
                "uid": doc.uid or doc.contact_id,  # ใช้ uid แทน contact_id ถ้ามี
                "firstname": doc.first_name,
                "lastname": doc.last_name,
                "gender": doc.gender_sd,
                "mom_birthdate": doc.birth_date,
                "phonenumber": doc.phone,
                "email": doc.email,
                "line_mid": doc.line_mid,
                "addressline1": doc.address,
                "region": doc.province_name,
                "city": doc.amphur_name,
                "addressline2": doc.sub_district_name,
                "zip": doc.postal_code,
                "income": doc.income,
                "contact_source": doc.contact_source,
                "data_source_code": doc.data_source_code,
                "brand": doc.brand or "WYETH",
                "status": doc.status or 1,
                "nestle_agent_referral_code": doc.nestle_agent_referral_code,
                "date_registration": doc.date_registration,
                "last_updated": doc.last_updated,
                # ใช้ข้อมูลจาก marketing_consent ถ้ามี ถ้าไม่มีให้ใช้จาก main profile
                "Is_MKT_Subscribed": (marketing_consent.get("is_consented") if marketing_consent else doc.is_consented) or "No",
                "MKT_Subscribed_Date": marketing_consent.get("consent_date") if marketing_consent else doc.marketing_subscribed_date,
                "MKT_Subscribed_Version": marketing_consent.get("consent_version") if marketing_consent else doc.marketing_subscribed_version,
              
                "consent_date": privacy_consent.get("consent_date") if privacy_consent else None,
                "consent_version": privacy_consent.get("consent_version") if privacy_consent else None,
                # ฟิลด์เกี่ยวกับเด็กที่อยู่ในระดับบนสุด ไม่ได้อยู่ในอาเรย์ child
                "child_birthdatereliability": doc.child_birthdatereliability,
                "gg_hospital": doc.gg_hospital,
                "gg_child_delivery_type": doc.gg_child_delivery_type,
                "gg_milk_currently_consuming": doc.gg_milk_currently_consuming
            }
            
            # เพิ่มข้อมูลเด็กทั้งหมด
            children_data = []
            for child_id in child_ids:
                child_doc = frappe.get_doc("ETL Child", child_id)
                child_data = {
                    "child_uid": child_doc.cusid,  # เปลี่ยนจาก child_id เป็น child_uid
                    "child_firstname": child_doc.nname,
                    "child_birthdate": child_doc.birthdate,
                    "child_add_date": child_doc.createdate,
                    "pc_code": child_doc.pc_code or "-",
                    "reason": child_doc.reason
                }
                children_data.append(child_data)
            
            if children_data:
                outbound_data["child"] = children_data
            
            # เพิ่มข้อมูล campaign/externalApplication
            campaign_data = []
            for campaign_id in campaign_ids:
                campaign_doc = frappe.get_doc("ETL Campaign", campaign_id)
                campaign_item = {
                    "applicationCode": campaign_doc.application_code,
                    "internaIdentifier": campaign_doc.internal_id,
                    "internalAlternateIdentifier": campaign_doc.internal_alternate_id,
                    "createDate": campaign_doc.create_date,
                    "lastUpdateDate": campaign_doc.last_update_date
                }
                campaign_data.append(campaign_item)
            
            if campaign_data:
                outbound_data["externalApplication"] = campaign_data
            
            # บันทึก outbound data
            # ดึงค่า webhook URL จากการตั้งค่าระบบ
            webhook_url = frappe.db.get_single_value("DH Setting", "crm_webhook_url") or ""
            webhook_api_key = frappe.db.get_single_value("DH Setting", "crm_api_key") or "default-key"

            outbound_doc = frappe.get_doc({
                "doctype": "DH Webhook Outbound",
                "profile_id": profile_id,
                "sent_to": "CRM",
                "webhook_url": webhook_url,
                "payload": frappe.as_json(outbound_data),
                "headers": frappe.as_json({
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {webhook_api_key}"
                }),
                "status": "Pending" if webhook_url else "Draft"
            })
            outbound_doc.insert(ignore_permissions=True)
            
            # อัพเดท sync log
            if log_id:
                log_doc = frappe.get_doc(self.parent.sync_log_doctype, log_id)
                log_doc.status = "Completed"
                log_doc.total_records = 1
                log_doc.processed_records = 1
                log_doc.processing_result = frappe.as_json({
                    "profile_id": profile_id,
                    "children": child_ids,
                    "campaigns": campaign_ids,
                    "consents": consent_ids,
                    "outbound": outbound_doc.name
                })
                log_doc.save(ignore_permissions=True)
            
            return {
                "status": "success",
                "message": "Profile synced successfully",
                "profile": profile_id,
                "children": child_ids,
                "campaigns": campaign_ids,
                "consents": consent_ids,
                "outbound": outbound_doc.name
            }
            
        except Exception as e:
            frappe.log_error(message=f"IC360 sync error: {str(e)}\n{frappe.get_traceback()}", title="IC360 Sync Error")
            
            # อัพเดท sync log
            if log_id:
                try:
                    log_doc = frappe.get_doc(self.parent.sync_log_doctype, log_id)
                    log_doc.status = "Failed"
                    log_doc.error_log = str(e)
                    log_doc.save(ignore_permissions=True)
                except:
                    pass
                
            return {"status": "error", "message": str(e)}
            
        finally:
            # ปิดการเชื่อมต่อ
            self.client.disconnect()

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
            