"""
Example of using PG Logger in Frappe hooks

Add these functions to your hooks.py file to automatically log 
document changes to PostgreSQL.
"""

import frappe
from datahubv2.lib.pg_connect import log_before_after_to_postgres


def log_document_changes(doc, method):
    """
    Hook function to log document changes to PostgreSQL
    
    Usage in hooks.py:
    doc_events = {
        "Sales Order": {
            "on_update": "datahubv2.lib.pg_connect.hooks_example.log_document_changes"
        }
    }
    """
    
    try:
        # Get the old document if it exists
        if doc.is_new():
            before_data = {}
        else:
            old_doc = frappe.get_doc(doc.doctype, doc.name)
            before_data = old_doc.as_dict()
        
        after_data = doc.as_dict()
        
        # Log the change
        success = log_before_after_to_postgres(
            ref_id=doc.name,
            ref_module=doc.doctype.lower().replace(" ", "_"),
            before_data=before_data,
            after_data=after_data
        )
        
        if not success:
            frappe.log_error(
                f"Failed to log document changes for {doc.doctype} {doc.name}",
                "PostgreSQL Logging Error"
            )
            
    except Exception as e:
        frappe.log_error(
            f"Exception in log_document_changes: {str(e)}",
            "PostgreSQL Logging Exception"
        )


def log_sales_order_update(doc, method):
    """
    Specific hook for Sales Order updates
    
    Usage in hooks.py:
    doc_events = {
        "Sales Order": {
            "on_update": "datahubv2.lib.pg_connect.hooks_example.log_sales_order_update"
        }
    }
    """
    
    try:
        # Only log certain status changes
        important_fields = ['status', 'grand_total', 'customer', 'delivery_date']
        
        if doc.has_value_changed(important_fields):
            old_values = {}
            new_values = {}
            
            for field in important_fields:
                old_values[field] = doc.get_db_value(field)
                new_values[field] = doc.get(field)
            
            success = log_before_after_to_postgres(
                ref_id=doc.name,
                ref_module="sales_order",
                before_data=old_values,
                after_data=new_values
            )
            
            if success:
                frappe.logger().info(f"Logged Sales Order update: {doc.name}")
                
    except Exception as e:
        frappe.log_error(f"Sales Order logging error: {str(e)}", "PostgreSQL Sales Order Log")


def log_custom_event(ref_id, module_name, event_data):
    """
    Custom event logging function
    
    Usage:
    from datahubv2.lib.pg_connect.hooks_example import log_custom_event
    
    log_custom_event(
        ref_id="CUSTOM-001",
        module_name="custom_module",
        event_data={
            "action": "data_sync",
            "records_processed": 150,
            "status": "success"
        }
    )
    """
    
    try:
        from datahubv2.lib.pg_connect import log_to_postgres
        
        success = log_to_postgres(
            ref_id=ref_id,
            ref_module=module_name,
            json_data=event_data
        )
        
        return success
        
    except Exception as e:
        frappe.log_error(f"Custom event logging error: {str(e)}", "PostgreSQL Custom Event Log")
        return False


def log_api_request(ref_id, endpoint, request_data, response_data, status_code=200):
    """
    Log API requests and responses
    
    Usage in API methods:
    from datahubv2.lib.pg_connect.hooks_example import log_api_request
    
    @frappe.whitelist()
    def my_api():
        # ... API logic ...
        
        log_api_request(
            ref_id=frappe.generate_hash(length=10),
            endpoint="my_api",
            request_data=frappe.local.request.args,
            response_data=response,
            status_code=200
        )
    """
    
    try:
        from datahubv2.lib.pg_connect import log_to_postgres
        
        log_data = {
            "endpoint": endpoint,
            "request": request_data,
            "response": response_data,
            "status_code": status_code,
            "user": frappe.session.user,
            "timestamp": frappe.utils.now(),
            "ip_address": frappe.local.request.environ.get('REMOTE_ADDR')
        }
        
        success = log_to_postgres(
            ref_id=ref_id,
            ref_module="api_log",
            json_data=log_data
        )
        
        return success
        
    except Exception as e:
        frappe.log_error(f"API request logging error: {str(e)}", "PostgreSQL API Log")
        return False


def log_background_job(job_name, job_data, result_data, status="success"):
    """
    Log background job execution
    
    Usage in background jobs:
    from datahubv2.lib.pg_connect.hooks_example import log_background_job
    
    def my_background_job():
        # ... job logic ...
        
        log_background_job(
            job_name="data_sync_job",
            job_data={"source": "external_api", "batch_size": 100},
            result_data={"processed": 100, "errors": 0},
            status="success"
        )
    """
    
    try:
        from datahubv2.lib.pg_connect import log_to_postgres
        
        log_data = {
            "job_name": job_name,
            "input": job_data,
            "output": result_data,
            "status": status,
            "executed_by": frappe.session.user,
            "execution_time": frappe.utils.now()
        }
        
        success = log_to_postgres(
            ref_id=f"{job_name}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}",
            ref_module="background_job",
            json_data=log_data
        )
        
        return success
        
    except Exception as e:
        frappe.log_error(f"Background job logging error: {str(e)}", "PostgreSQL Job Log")
        return False


# Example hooks.py configuration:
"""
# Add to your hooks.py file:

doc_events = {
    "Sales Order": {
        "on_update": "datahubv2.lib.pg_connect.hooks_example.log_sales_order_update"
    },
    "Customer": {
        "on_update": "datahubv2.lib.pg_connect.hooks_example.log_document_changes"
    },
    # Add more doctypes as needed
}

# For API logging, add to your API methods:
@frappe.whitelist()
def my_api_method():
    try:
        # Your API logic here
        result = {"status": "success", "data": "some data"}
        
        # Log the API call
        from datahubv2.lib.pg_connect.hooks_example import log_api_request
        log_api_request(
            ref_id=frappe.generate_hash(length=10),
            endpoint="my_api_method",
            request_data=frappe.local.request.args,
            response_data=result
        )
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
"""