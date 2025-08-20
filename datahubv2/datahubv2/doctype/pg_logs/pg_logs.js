// Copyright (c) 2025, Ton and contributors
// For license information, please see license.txt

frappe.ui.form.on("PG Logs", {
    refresh(frm) {
        // Add Test Connection button
        frm.add_custom_button(__('Test Connection'), function() {
            test_pg_connection(frm);
        }, __('Actions'));
    },
});

function test_pg_connection(frm) {
    // Validate required fields
    const required_fields = ['host', 'port', 'db_name', 'user_name', 'password'];
    let missing_fields = [];
    
    required_fields.forEach(field => {
        if (!frm.doc[field]) {
            missing_fields.push(field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()));
        }
    });
    
    if (missing_fields.length > 0) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('The following fields are required for testing connection: ') + missing_fields.join(', '),
            indicator: 'red'
        });
        return;
    }
    
    // Show loading indicator
    frappe.show_alert({
        message: __('Testing PostgreSQL connection...'),
        indicator: 'blue'
    });
    
    // Call server method to test connection
    frappe.call({
        method: 'datahubv2.datahubv2.doctype.pg_logs.pg_logs.test_postgresql_connection',
        args: {
            host: frm.doc.host,
            port: frm.doc.port,
            db_name: frm.doc.db_name,
            user_name: frm.doc.user_name,
            password: frm.doc.password
        },
        callback: function(response) {
            if (response.message) {
                const result = response.message;
                
                if (result.success) {
                    // Success message
                    frappe.msgprint({
                        title: __('PostgreSQL Connection Test Successful'),
                        message: `
                            <div class="alert alert-success">
                                <strong>✓ PostgreSQL connection successful!</strong><br>
                                <strong>Host:</strong> ${result.host}:${result.port}<br>
                                <strong>Database:</strong> ${result.database}<br>
                                <strong>Server Version:</strong> ${result.server_version || 'Unknown'}<br>
                                <strong>Response Time:</strong> ${result.response_time}ms<br>
                                ${result.tables_count ? `<strong>Tables Found:</strong> ${result.tables_count}<br>` : ''}
                                <br><small><em>Connection tested at: ${result.tested_at}</em></small>
                            </div>
                        `,
                        indicator: 'green'
                    });
                } else {
                    // Error message
                    frappe.msgprint({
                        title: __('PostgreSQL Connection Test Failed'),
                        message: `
                            <div class="alert alert-danger">
                                <strong>✗ PostgreSQL connection failed!</strong><br>
                                <strong>Host:</strong> ${result.host}:${result.port}<br>
                                <strong>Database:</strong> ${result.database}<br>
                                <strong>Error:</strong> ${result.error}<br>
                                <strong>Response Time:</strong> ${result.response_time}ms<br>
                                <br><small><em>Connection tested at: ${result.tested_at}</em></small>
                            </div>
                        `,
                        indicator: 'red'
                    });
                }
            }
        },
        error: function(xhr) {
            frappe.msgprint({
                title: __('Test Failed'),
                message: __('An error occurred while testing the PostgreSQL connection. Please check the console for details.'),
                indicator: 'red'
            });
            console.error('PostgreSQL connection test error:', xhr);
        }
    });
}
