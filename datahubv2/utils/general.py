import frappe
from collections import namedtuple

FormulaLookup = namedtuple('FormulaLookup', ['value', 'description'])

def get_lookup_formula(source, source_key) -> FormulaLookup:
    """Get formula lookup value and description
    
    Args:
        source: Source of the formula
        source_key: Source key to lookup
        
    Returns:
        FormulaLookup: Named tuple containing value and description
    """
    try:
        ret = frappe.get_value(
            "DH Lookup Formula",
            {
                "source": source, 
                "source_key": source_key
            },
            ["target_value", "source_desc"],
            as_dict=True
        )
        
        if not ret:
            return FormulaLookup("", "")
            
        return FormulaLookup(
            ret.get("target_value", ""),
            ret.get("source_desc", "")
        )
        
    except Exception as e:
        frappe.log_error(title="Error getting mapping value", message=f"Error getting mapping value: {str(e)}")
        return FormulaLookup("", "")

def get_lookup_data(source, code, source_id):
    try:
        ret = frappe.get_value(
            "DH Lookup Data", 
            {
                "source": source,
                "code": code,
                "source_id": source_id
            },
            "target_value"
        )
        return ret or ""
    except Exception as e:
        frappe.log_error(title="Error getting lookup data", message=f"Error getting lookup data: {str(e)}")
        return None
