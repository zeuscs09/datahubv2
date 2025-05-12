frappe.ui.form.on('DH Webhook Inbound', {
    refresh: function(frm) {
        // Add custom buttons
        // if (frm.doc.status === "Received") {
        //     frm.add_custom_button(__('Validate'), function() {
        //         frm.trigger('validate_webhook');
        //     });
        // }
        
        // if (frm.doc.status === "Validated") {
        //     frm.add_custom_button(__('Process'), function() {
        //         frm.trigger('process_webhook');
        //     });
        // }
        
        // if (frm.doc.status === "Processing") {
        //     frm.add_custom_button(__('Complete'), function() {
        //         frm.trigger('complete_webhook');
        //     });
        // }
        
        // if (frm.doc.status === "Failed") {
        //     frm.add_custom_button(__('Retry'), function() {
        //         frm.trigger('retry_webhook');
        //     });
        // }

        if (frm.doc.status === 'Received' || frm.doc.status === 'Validated' || frm.doc.status === 'Failed') {
            frm.add_custom_button(__('Sync'), function() {
                frappe.call({
                    freeze: true,
                    freeze_message: __('Syncing webhook...'),
                    method: 'datahubv2.api.v1.inbound.sync_webhook',
                    args: {
                        inbound_id: frm.doc.inbound_id
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Webhook synced successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
    },

    inbound_id: function(frm) {
        // Validate inbound_id format
        if (frm.doc.inbound_id && !frm.doc.inbound_id.match(/^INB-\d{14}$/)) {
            frappe.msgprint("Inbound ID must be in format: INB-YYYYMMDDHHMMSS");
            frm.set_value('inbound_id', '');
        }
    },

    source_ip: function(frm) {
        // Validate IP address format
        if (frm.doc.source_ip) {
            const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
            if (!ipRegex.test(frm.doc.source_ip)) {
                frappe.msgprint("Invalid IP address format");
                frm.set_value('source_ip', '');
            }
        }
    },

    status: function(frm) {
        // Validate status transitions
        const validTransitions = {
            "Received": ["Validated", "Failed"],
            "Validated": ["Processing", "Failed"],
            "Processing": ["Completed", "Failed"],
            "Completed": [],
            "Failed": ["Received"]
        };
        
        if (frm.doc.__islocal) return;
        
        const currentStatus = frm.doc.status;
        const previousStatus = frm.doc.__previous_status;
        
        if (previousStatus && !validTransitions[previousStatus].includes(currentStatus)) {
            frappe.msgprint(`Invalid status transition from ${previousStatus} to ${currentStatus}`);
            frm.set_value('status', previousStatus);
        }
    },

    payload: function(frm) {
        // Validate payload is valid JSON
        if (frm.doc.payload) {
            try {
                JSON.parse(frm.doc.payload);
            } catch (e) {
                frappe.msgprint("Payload must be valid JSON");
                frm.set_value('payload', '');
            }
        }
    },

    headers: function(frm) {
        // Validate headers is valid JSON
        if (frm.doc.headers) {
            try {
                JSON.parse(frm.doc.headers);
            } catch (e) {
                frappe.msgprint("Headers must be valid JSON");
                frm.set_value('headers', '');
            }
        }
    },

    validation_result: function(frm) {
        // Validate validation_result is valid JSON
        if (frm.doc.validation_result) {
            try {
                JSON.parse(frm.doc.validation_result);
            } catch (e) {
                frappe.msgprint("Validation Result must be valid JSON");
                frm.set_value('validation_result', '');
            }
        }
    },

    validate_webhook: function(frm) {
        // Validate webhook data
        frappe.call({
            method: 'validate_hmac',
            doc: frm.doc,
            args: {
                secret_key: frappe.boot.webhook_secret_key
            },
            callback: function(r) {
                if (r.message) {
                    frm.trigger('update_status', 'Validated');
                } else {
                    frm.trigger('set_error', 'HMAC validation failed');
                }
            }
        });
    },

    process_webhook: function(frm) {
        // Process webhook data
        frm.trigger('update_status', 'Processing');
    },

    complete_webhook: function(frm) {
        // Complete webhook processing
        frm.trigger('update_status', 'Completed');
    },

    retry_webhook: function(frm) {
        // Retry failed webhook
        frm.trigger('update_status', 'Received');
    },

    update_status: function(frm, new_status) {
        // Update status
        frappe.call({
            method: 'update_status',
            doc: frm.doc,
            args: {
                new_status: new_status
            },
            callback: function(r) {
                if (r.message) {
                    frm.refresh();
                }
            }
        });
    },

    set_error: function(frm, error_message) {
        // Set error message
        frappe.call({
            method: 'set_error',
            doc: frm.doc,
            args: {
                error_message: error_message
            },
            callback: function(r) {
                if (r.message) {
                    frm.refresh();
                }
            }
        });
    }
}); 