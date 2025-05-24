from ..utils.general import get_lookup_formula, get_lookup_data
from ..lib.ic360.client import IC360Client
import frappe

def update_datahub_lookup(main_profile,child_data):
    
    """ค้นหาข้อมูลจาก main profile และ child profile"""
    ic360_client = IC360Client()
    main_profile.sourceid = get_lookup_data("SD","DataSourceCode",main_profile.data_source_code)

    main_profile.gender = get_lookup_data("SD","GENDER",main_profile.gender_sd)

    if main_profile.province_name and main_profile.amphur_name and main_profile.sub_district_name:
        area_info = ic360_client.get_area_info(
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
            child_profile.born_place_id = get_lookup_data("SD","NL_ANC_PLACE",child_profile.gg_hospital)
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
    
def update_sd_lookup(main_profile, child_profile):
    """ค้นหาข้อมูลจาก main profile และ child profile"""
    if main_profile:
        main_profile.data_source_code = get_lookup_data("IC360", "DataSourceCode", main_profile.sourceid)
        main_profile.gender_sd = get_lookup_data("IC360", "GENDER", main_profile.gender)
        main_profile.save(ignore_permissions=True)
    
    if child_profile:
        child_profile.gg_child_delivery_type = get_lookup_data("IC360", "NL_BIRTH_PLAN", child_profile.birth_plan)
        child_profile.gg_hospital = get_lookup_data("IC360", "NL_ANC_PLACE", child_profile.born_place_id)
        child_profile.child_birthdatereliability = get_lookup_data("IC360", "NL_MOTHERSTAGE", child_profile.mother_stage)
    
        if child_profile.lastpro and child_profile.lastformula:
            # แปลงเป็น string เพื่อป้องกันข้อผิดพลาดในการรวม string
            lastpro_str = str(child_profile.lastpro) if child_profile.lastpro is not None else ""
            lastformula_str = str(child_profile.lastformula) if child_profile.lastformula is not None else ""
            lastpro_key = lastpro_str + "-" + lastformula_str
            child_profile.gg_milk_currently_consuming = get_lookup_formula("IC360", lastpro_key)
        
        child_profile.save(ignore_permissions=True)
    