frappe.ui.form.on('DH Webhook Outbound', {
    refresh: function(frm) {
        // เพิ่มปุ่ม Manual Send สำหรับ record ที่ status เป็น Pending หรือ Failed
        if (frm.doc.name && (frm.doc.status === 'Pending' || frm.doc.status === 'Failed')) {
            frm.add_custom_button(__('🚀 Manual Send'), function() {
                send_webhook_manual(frm);
            }, __('Actions'));
        }
        
        // เพิ่มปุ่ม Retry สำหรับ record ที่ status เป็น Failed
        if (frm.doc.name && frm.doc.status === 'Failed') {
            frm.add_custom_button(__('🔄 Retry'), function() {
                retry_webhook(frm);
            }, __('Actions'));
        }
        
        // เพิ่มปุ่ม View Logs สำหรับดู detailed logs
        if (frm.doc.name) {
            frm.add_custom_button(__('📋 View Logs'), function() {
                view_webhook_logs(frm);
            }, __('Actions'));
        }
    }
});

function send_webhook_manual(frm) {
    /**
     * ส่ง webhook ด้วยตนเอง
     */
    let webhook_type = frm.doc.sent_to && frm.doc.sent_to.startsWith('SD') ? 'SD (via Proxy)' : 'Direct';
    
    frappe.confirm(
        __(`คุณต้องการส่ง webhook นี้ด้วยตนเองหรือไม่?<br/><br/>
           <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
               <strong>📡 Webhook Details:</strong><br/>
               • <strong>ID:</strong> ${frm.doc.outbound_id || 'N/A'}<br/>
               • <strong>Target:</strong> ${frm.doc.sent_to || 'Unknown'}<br/>
               • <strong>URL:</strong> ${frm.doc.webhook_url || 'N/A'}<br/>
               • <strong>Method:</strong> ${webhook_type}<br/>
               • <strong>Status:</strong> ${frm.doc.status || 'Unknown'}
           </div>
           <div style="color: #856404; background: #fff3cd; padding: 8px; border-radius: 4px;">
               <strong>⚠️ หมายเหตุ:</strong> การส่งจะใช้การตั้งค่า proxy ปัจจุบันสำหรับ SD webhooks
           </div>`),
        function() {
            frappe.call({
                method: 'datahubv2.core.hook.manual_send_webhook',
                args: {
                    webhook_name: frm.doc.name
                },
                freeze: true,
                freeze_message: __('🚀 กำลังส่ง webhook...<br/>กรุณารอสักครู่'),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: 'green'
                            });
                            
                            // แสดงรายละเอียดผลลัพธ์
                            let result_html = `
                                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                                    <div style="text-align: center; margin-bottom: 20px;">
                                        <div style="font-size: 48px; color: #28a745;">🚀</div>
                                        <h3 style="color: #28a745; margin: 10px 0;">Webhook ส่งสำเร็จ!</h3>
                                    </div>
                                    
                                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>📡 Webhook ID:</strong></span>
                                            <span style="color: #007bff; font-weight: bold;">${frm.doc.outbound_id}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>🎯 Target:</strong></span>
                                            <span style="color: #6f42c1; font-weight: bold;">${frm.doc.sent_to}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>📊 Response Code:</strong></span>
                                            <span style="color: #28a745; font-weight: bold;">${r.message.response_code || 'N/A'}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between;">
                                            <span><strong>🕒 Sent At:</strong></span>
                                            <span style="color: #fd7e14; font-weight: bold;">${r.message.sent_at || 'N/A'}</span>
                                        </div>
                                    </div>
                                    
                                    <div style="padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;">
                                        <strong>✨ Webhook ส่งสำเร็จแล้ว!</strong><br/>
                                        สถานะได้รับการอัพเดทเป็น "Sent"
                                    </div>
                                </div>
                            `;
                            
                            frappe.msgprint({
                                title: __('🎉 Manual Send Results'),
                                message: result_html,
                                indicator: 'green',
                                wide: true
                            });
                            
                        } else {
                            frappe.msgprint({
                                title: __('❌ Webhook ส่งล้มเหลว'),
                                message: `
                                    <div style="text-align: center; margin-bottom: 15px;">
                                        <div style="font-size: 48px; color: #dc3545;">🚀</div>
                                        <h4 style="color: #dc3545;">ไม่สามารถส่ง webhook ได้</h4>
                                    </div>
                                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; color: #721c24;">
                                        <strong>Error:</strong><br/>
                                        ${r.message.message}
                                    </div>
                                    <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-radius: 4px; color: #0c5460;">
                                        <strong>💡 แนวทางแก้ไข:</strong><br/>
                                        • ตรวจสอบ webhook URL<br/>
                                        • ตรวจสอบ payload และ headers<br/>
                                        • ตรวจสอบการเชื่อมต่อ network<br/>
                                        • ตรวจสอบ proxy settings (สำหรับ SD webhooks)
                                    </div>
                                `,
                                indicator: 'red',
                                wide: true
                            });
                        }
                        
                        // Refresh form เพื่อแสดงข้อมูลใหม่
                        frm.reload_doc();
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('⚠️ เกิดข้อผิดพลาดระหว่างการเชื่อมต่อ'),
                        message: `
                            <div style="text-align: center; margin-bottom: 15px;">
                                <div style="font-size: 48px; color: #ffc107;">⚠️</div>
                                <h4 style="color: #856404;">ไม่สามารถเชื่อมต่อ API ได้</h4>
                            </div>
                            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; color: #856404;">
                                ไม่สามารถส่ง webhook ได้ อาจเกิดจาก:<br/>
                                • ปัญหาการเชื่อมต่อ network<br/>
                                • API Server ไม่ตอบสนอง<br/>
                                • ปัญหา proxy server (สำหรับ SD webhooks)
                            </div>
                        `,
                        indicator: 'red',
                        wide: true
                    });
                }
            });
        }
    );
}

function retry_webhook(frm) {
    /**
     * ลองส่ง webhook อีกครั้ง
     */
    frappe.confirm(
        __(`คุณต้องการลองส่ง webhook นี้อีกครั้งหรือไม่?<br/><br/>
           <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; color: #856404;">
               <strong>🔄 Retry Information:</strong><br/>
               • Current retry count: ${frm.doc.retry_count || 0}<br/>
               • Last error: ${frm.doc.error_message || 'Unknown error'}
           </div>`),
        function() {
            send_webhook_manual(frm);
        }
    );
}

function view_webhook_logs(frm) {
    /**
     * ดู logs ของ webhook นี้
     */
    frappe.call({
        method: 'datahubv2.core.hook.get_webhook_logs',
        args: {
            webhook_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let logs_html = `
                    <div style="font-family: monospace; font-size: 12px;">
                        <h4>📋 Webhook Logs: ${frm.doc.outbound_id}</h4>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 400px; overflow-y: auto;">
                `;
                
                if (r.message.logs && r.message.logs.length > 0) {
                    r.message.logs.forEach(function(log) {
                        logs_html += `
                            <div style="margin-bottom: 10px; padding: 8px; background: white; border-left: 4px solid #007bff; border-radius: 4px;">
                                <strong>${log.title}</strong><br/>
                                <small style="color: #666;">${log.creation}</small><br/>
                                <div style="margin-top: 5px;">${log.error}</div>
                            </div>
                        `;
                    });
                } else {
                    logs_html += '<div style="text-align: center; color: #666;">ไม่พบ logs สำหรับ webhook นี้</div>';
                }
                
                logs_html += '</div></div>';
                
                frappe.msgprint({
                    title: __('📋 Webhook Logs'),
                    message: logs_html,
                    wide: true
                });
            }
        }
    });
} 