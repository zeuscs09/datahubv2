frappe.ui.form.on('ETL Sync Log', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.status === "Processing") {
            frm.add_custom_button(__('Refresh Progress'), function() {
                frm.trigger('update_progress');
            });
        }
    },

    validate: function(frm) {
        // Add additional client-side validation here
    },

    sync_id: function(frm) {
        // Auto-generate sync_id if empty
        if (!frm.doc.sync_id) {
            frm.set_value('sync_id', frappe.utils.get_random(10));
        }
    },

    sync_type: function(frm) {
        // Update fields based on sync type
        if (frm.doc.sync_type === 'PENDING') {
            frm.set_value('status', 'Pending');
        } else if (frm.doc.sync_type === 'MIGRATION') {
            frm.set_value('status', 'Processing');
        }
    },

    sync_date: function(frm) {
        // Validate sync date
        if (frm.doc.sync_date && frm.doc.sync_date > frappe.datetime.now_datetime()) {
            frappe.throw('Sync Date cannot be in the future');
        }
    },

    status: function(frm) {
        // Update processed records when status changes
        if (frm.doc.status === 'Completed') {
            frm.set_value('processed_records', frm.doc.total_records);
        }
    },

    error_log: function(frm) {
        // Validate error log is valid JSON
        if (frm.doc.error_log) {
            try {
                JSON.parse(frm.doc.error_log);
            } catch (e) {
                frappe.msgprint("Error Log must be valid JSON");
                frm.set_value('error_log', '');
            }
        }
    },

    raw_data: function(frm) {
        // Validate raw data is valid JSON
        if (frm.doc.raw_data) {
            try {
                JSON.parse(frm.doc.raw_data);
            } catch (e) {
                frappe.msgprint("Raw Data must be valid JSON");
                frm.set_value('raw_data', '');
            }
        }
    },

    update_progress: function(frm) {
        // Update progress from server
        frappe.call({
            method: 'get_progress',
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.set_value('processed_records', r.message.processed);
                    frm.set_value('success_records', r.message.success);
                    frm.set_value('failed_records', r.message.failed);
                    frm.set_value('status', r.message.status);
                    frm.refresh();
                }
            }
        });
    },

    start_sync: function(frm, total_records) {
        // Start sync process
        frappe.call({
            method: 'start_sync',
            doc: frm.doc,
            args: {
                total_records: total_records
            },
            callback: function(r) {
                if (r.message) {
                    frm.refresh();
                }
            }
        });
    },

    log_error: function(frm, error_data) {
        // Log error details
        frappe.call({
            method: 'log_error',
            doc: frm.doc,
            args: {
                error_data: error_data
            },
            callback: function(r) {
                if (r.message) {
                    frm.refresh();
                }
            }
        });
    }
}); 