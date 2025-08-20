// Copyright (c) 2025, Ton and contributors
// For license information, please see license.txt

frappe.ui.form.on('DH Incident API Config', {
    refresh: function(frm) {
        // เพิ่มปุ่ม Manual Sync
        frm.add_custom_button(__('Manual Sync'), function() {
            sync_incidents_manually(frm);
        }, __('SD Incident'));
        
        // // เพิ่มปุ่ม Test Query (สำหรับทดสอบ SQL Query)
        // frm.add_custom_button(__('Test Query'), function() {
        //     test_sql_query(frm);
        // }, __('SD Incident'));
        
        // // เพิ่มปุ่ม Debug Query (สำหรับดู query ที่จะใช้ sync จริง)
        // frm.add_custom_button(__('Debug Query'), function() {
        //     debug_sync_query(frm);
        // }, __('SD Incident'));
        
        // // เพิ่มปุ่ม Reset Last Sync
        // frm.add_custom_button(__('Reset Last Sync'), function() {
        //     reset_last_sync(frm);
        // }, __('SD Incident'));
        
        // เพิ่มปุ่ม Test IC360 Connection
        frm.add_custom_button(__('Test IC360 Connection'), function() {
            test_ic360_connection(frm);
        }, __('SD Incident'));
        
        // เพิ่มปุ่ม Get Token
        frm.add_custom_button(__('Get Token'), function() {
            refresh_auth_token(frm);
        }, __('SD Incident'));
        
        // ถ้าไม่ได้บันทึกแล้ว ให้ปิดใช้งานปุ่ม
        if (frm.is_new()) {
            frm.disable_save();
        }
    },
    
    // Validate ก่อนบันทึก
    validate: function(frm) {
        if (!frm.doc.sql_query) {
            frappe.throw(__('SQL Query is required'));
        }
        
        if (!frm.doc.url_endpoint) {
            frappe.throw(__('URL Endpoint is required'));
        }
        
        if (!frm.doc.username) {
            frappe.throw(__('Username is required for API authentication'));
        }
        
        if (!frm.doc.password) {
            frappe.throw(__('Password is required for API authentication'));
        }
        
        if (frm.doc.header) {
            try {
                JSON.parse(frm.doc.header);
            } catch (e) {
                frappe.throw(__('Header must be valid JSON'));
            }
        }
        
        if (!frm.doc.chunk_size || frm.doc.chunk_size <= 0) {
            frappe.throw(__('Chunk Size must be a positive number'));
        }
    }
});

function sync_incidents_manually(frm) {
    frappe.confirm(
        __('คุณต้องการ sync ข้อมูล incidents ไป SD หรือไม่?'),
        function() {
            frappe.call({
                method: 'datahubv2.core.sd_incident.service.manual_sync_incidents',
                freeze: true,
                freeze_message: __('🔄 กำลัง Sync ข้อมูล incidents ไป SD...<br/><br/>กรุณารอสักครู่'),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: 'green'
                            });
                            
                            // แสดงรายละเอียดเพิ่มเติม
                            let summary_html = `
                                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                                    <div style="text-align: center; margin-bottom: 20px;">
                                        <div style="font-size: 48px; color: #28a745;">✅</div>
                                        <h3 style="color: #28a745; margin: 10px 0;">Sync เสร็จสิ้น!</h3>
                                    </div>
                                    
                                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>📊 จำนวนข้อมูล:</strong></span>
                                            <span style="color: #007bff; font-weight: bold;">${r.message.records_processed || 0} records</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>📦 จำนวน chunks:</strong></span>
                                            <span style="color: #6f42c1; font-weight: bold;">${r.message.chunks_created || 0} chunks</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between;">
                                            <span><strong>🔗 Webhook documents:</strong></span>
                                            <span style="color: #fd7e14; font-weight: bold;">${(r.message.outbound_docs || []).length} docs</span>
                                        </div>
                                    </div>
                                    
                                    ${r.message.records_processed > 0 ? 
                                        '<div style="padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;"><strong>✨ ข้อมูลถูกส่งไป SD แล้ว!</strong><br/>สามารถตรวจสอบสถานะใน DH Webhook Outbound</div>' :
                                        '<div style="padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;"><strong>ℹ️ ไม่มีข้อมูลใหม่</strong><br/>ลองตรวจสอบ Last Sync หรือ SQL Query</div>'
                                    }
                                </div>
                            `;
                            
                            frappe.msgprint({
                                title: __('🎉 Manual Sync Results'),
                                message: summary_html,
                                indicator: 'green',
                                wide: true
                            });
                        } else {
                            frappe.msgprint({
                                title: __('❌ Sync ล้มเหลว'),
                                message: `
                                    <div style="text-align: center; margin-bottom: 15px;">
                                        <div style="font-size: 48px; color: #dc3545;">❌</div>
                                        <h4 style="color: #dc3545;">เกิดข้อผิดพลาด</h4>
                                    </div>
                                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; color: #721c24;">
                                        <strong>Error:</strong><br/>
                                        ${r.message.message}
                                    </div>
                                    <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-radius: 4px; color: #0c5460;">
                                        <strong>💡 แนวทางแก้ไข:</strong><br/>
                                        • ตรวจสอบ Error Log ใน Frappe<br/>
                                        • ตรวจสอบ SQL Query และ last_sync<br/>
                                        • ลองปุ่ม "Test IC360 Connection"
                                    </div>
                                `,
                                indicator: 'red',
                                wide: true
                            });
                        }
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('⚠️ เกิดข้อผิดพลาดระหว่างการเชื่อมต่อ'),
                        message: `
                            <div style="text-align: center; margin-bottom: 15px;">
                                <div style="font-size: 48px; color: #ffc107;">⚠️</div>
                                <h4 style="color: #856404;">ไม่สามารถเชื่อมต่อได้</h4>
                            </div>
                            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; color: #856404;">
                                ไม่สามารถ sync ข้อมูลได้ อาจเกิดจาก:<br/>
                                • ปัญหาการเชื่อมต่อ network<br/>
                                • Server ไม่ตอบสนอง<br/>
                                • การตั้งค่า API ไม่ถูกต้อง
                            </div>
                            <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-radius: 4px; color: #0c5460;">
                                <strong>🔧 ขั้นตอนแก้ไข:</strong><br/>
                                1. ตรวจสอบ console log (F12)<br/>
                                2. ตรวจสอบ Error Log ใน Frappe<br/>
                                3. ลองปุ่ม "Test IC360 Connection"
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

function refresh_auth_token(frm) {
    if (!frm.doc.username || !frm.doc.password) {
        frappe.throw(__('กรุณาใส่ Username และ Password ก่อน'));
        return;
    }
    
    if (!frm.doc.url_endpoint) {
        frappe.throw(__('กรุณาใส่ URL Endpoint ก่อน'));
        return;
    }
    
    frappe.confirm(
        __('คุณต้องการ refresh token จาก API หรือไม่?<br/><br/>ระบบจะ login ด้วย username/password ที่ตั้งค่าไว้ และอัพเดท token ใน header'),
        function() {
            frappe.call({
                method: 'datahubv2.core.sd_incident.service.refresh_auth_token',
                freeze: true,
                freeze_message: __('🔑 กำลัง Login และดึง Token...<br/>กรุณารอสักครู่'),
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
                                        <div style="font-size: 48px; color: #28a745;">🔑</div>
                                        <h3 style="color: #28a745; margin: 10px 0;">Token Refresh สำเร็จ!</h3>
                                    </div>
                                    
                                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>🔐 Login Status:</strong></span>
                                            <span style="color: #28a745; font-weight: bold;">${r.message.login_attempted ? '✅ สำเร็จ' : '❌ ไม่ได้ลอง'}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>🎟️ Token Status:</strong></span>
                                            <span style="color: #007bff; font-weight: bold;">${r.message.token_received ? '✅ รับแล้ว' : '❌ ไม่ได้รับ'}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                            <span><strong>⚙️ Config Update:</strong></span>
                                            <span style="color: #6f42c1; font-weight: bold;">${r.message.config_updated ? '✅ อัพเดทแล้ว' : '❌ ไม่ได้อัพเดท'}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between;">
                                            <span><strong>🕒 Updated At:</strong></span>
                                            <span style="color: #fd7e14; font-weight: bold;">${r.message.updated_at || 'N/A'}</span>
                                        </div>
                                    </div>
                                    
                                    ${r.message.user_info && r.message.user_info.email ? 
                                        `<div style="padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;">
                                            <strong>👤 Logged in as:</strong> ${r.message.user_info.email}
                                        </div>` : ''
                                    }
                                    
                                    <div style="padding: 10px; background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; color: #0c5460; margin-top: 15px;">
                                        <strong>✨ Token ได้รับการอัพเดทแล้ว!</strong><br/>
                                        • Header ใน DH Incident API Config<br/>
                                        • sd_header ใน DH Setting (ถ้ามี)
                                    </div>
                                </div>
                            `;
                            
                            frappe.msgprint({
                                title: __('🎉 Token Refresh Results'),
                                message: result_html,
                                indicator: 'green',
                                wide: true
                            });
                            
                            // Refresh form เพื่อแสดงข้อมูลใหม่
                            frm.reload_doc();
                            
                        } else {
                            frappe.msgprint({
                                title: __('❌ Token Refresh ล้มเหลว'),
                                message: `
                                    <div style="text-align: center; margin-bottom: 15px;">
                                        <div style="font-size: 48px; color: #dc3545;">🔐</div>
                                        <h4 style="color: #dc3545;">ไม่สามารถ refresh token ได้</h4>
                                    </div>
                                    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; color: #721c24;">
                                        <strong>Error:</strong><br/>
                                        ${r.message.message}
                                    </div>
                                    <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-radius: 4px; color: #0c5460;">
                                        <strong>💡 แนวทางแก้ไข:</strong><br/>
                                        • ตรวจสอบ Username/Password ในหน้านี้<br/>
                                        • ตรวจสอบ URL Endpoint ที่ตั้งค่าไว้<br/>
                                        • ตรวจสอบการเชื่อมต่อ network<br/>
                                        • ตรวจสอบ Error Log ใน Frappe
                                    </div>
                                `,
                                indicator: 'red',
                                wide: true
                            });
                        }
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
                                ไม่สามารถ refresh token ได้ อาจเกิดจาก:<br/>
                                • ปัญหาการเชื่อมต่อ network<br/>
                                • API Server ไม่ตอบสนอง<br/>
                                • URL Endpoint ไม่ถูกต้อง
                            </div>
                            <div style="margin-top: 15px; padding: 10px; background: #d1ecf1; border-radius: 4px; color: #0c5460;">
                                <strong>🔧 ขั้นตอนแก้ไข:</strong><br/>
                                1. ตรวจสอบ console log (F12)<br/>
                                2. ตรวจสอบ Error Log ใน Frappe<br/>
                                3. ตรวจสอบ URL Endpoint และ network
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

// Note: ใช้ freeze: true ใน frappe.call แทนการเรียก frappe.freeze() โดยตรง
// เพราะ frappe.freeze() ไม่ใช่ standard function ใน Frappe Framework

function test_sql_query(frm) {
    if (!frm.doc.sql_query) {
        frappe.throw(__('กรุณาใส่ SQL Query ก่อน'));
        return;
    }
    
    frappe.confirm(
        __('คุณต้องการทดสอบ SQL Query นี้หรือไม่? (จะดึงข้อมูل 5 records แรกเท่านั้น)'),
        function() {
            frappe.call({
                method: 'datahubv2.core.sd_incident.service.test_sql_query',
                args: {
                    sql_query: frm.doc.sql_query
                },
                freeze: true,
                freeze_message: __('🧪 กำลังทดสอบ SQL Query...<br/>กรุณารอสักครู่'),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            let results = r.message.data || [];
                            
                            if (results.length === 0) {
                                frappe.msgprint({
                                    title: __('✅ Query ทำงานได้'),
                                    message: __('Query ทำงานปกติ แต่ไม่มีข้อมูลที่ตรงกับเงื่อนไข'),
                                    indicator: 'yellow'
                                });
                            } else {
                                // แสดงผลลัพธ์ในตาราง
                                let html = '<div style="max-height: 400px; overflow-y: auto;"><table class="table table-bordered">';
                                
                                // Headers
                                if (results.length > 0) {
                                    html += '<thead><tr>';
                                    Object.keys(results[0]).forEach(key => {
                                        html += `<th>${key}</th>`;
                                    });
                                    html += '</tr></thead>';
                                }
                                
                                // Data rows
                                html += '<tbody>';
                                results.forEach(row => {
                                    html += '<tr>';
                                    Object.values(row).forEach(value => {
                                        html += `<td>${value || ''}</td>`;
                                    });
                                    html += '</tr>';
                                });
                                html += '</tbody></table></div>';
                                
                                frappe.msgprint({
                                    title: __(`✅ Query ทำงานได้ - พบข้อมูล ${results.length} records`),
                                    message: html,
                                    indicator: 'green',
                                    wide: true
                                });
                            }
                        } else {
                            frappe.msgprint({
                                title: __('❌ Query มีปัญหา'),
                                message: r.message.message,
                                indicator: 'red'
                            });
                        }
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('⚠️ เกิดข้อผิดพลาด'),
                        message: __('ไม่สามารถทดสอบ Query ได้'),
                        indicator: 'red'
                    });
                }
            });
        }
    );
}

function debug_sync_query(frm) {
    frappe.call({
        method: 'datahubv2.core.sd_incident.service.debug_sync_query',
        freeze: true,
        freeze_message: __('🔍 กำลังดึงข้อมูล debug...<br/>กรุณารอสักครู่'),
        callback: function(r) {
            if (r.message) {
                if (r.message.success) {
                    let data = r.message.data;
                    
                    // สร้าง HTML สำหรับแสดงข้อมูล debug
                    let html = `
                        <div style="font-family: monospace;">
                            <h4>🔍 Debug Information</h4>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>📅 Last Sync:</strong><br/>
                                <code>${data.last_sync || 'NULL'}</code> (${data.last_sync_type})
                                ${data.default_date_used ? `<br/><span style="color: orange;">🔄 ใช้ default date: <code>${data.default_date_used}</code></span>` : ''}
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>📝 Original Query:</strong><br/>
                                <textarea readonly style="width:100%; height:80px; font-family:monospace;">${data.original_query}</textarea>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>⚡ Processed Query (ที่จะใช้ sync จริง):</strong><br/>
                                <textarea readonly style="width:100%; height:100px; font-family:monospace; background:#f8f9fa;">${data.processed_query}</textarea>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>🌐 URL Endpoint:</strong><br/>
                                <code>${data.url_endpoint}</code>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>📦 Chunk Size:</strong> ${data.chunk_size}
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>🔑 Header Keys:</strong><br/>
                                <code>${data.header_keys.join(', ')}</code>
                            </div>
                            
                            <div style="padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
                                <strong>💡 วิธีแก้ปัญหา "ไม่เจอข้อมูล":</strong><br/>
                                • หาก <code>last_sync</code> มีค่าวันที่ในอนาคต หรือหลังจากข้อมูลล่าสุด → ใช้ปุ่ม <strong>"Reset Last Sync"</strong><br/>
                                • หาก <code>last_sync</code> เป็น NULL → ระบบจะใช้ default date (30 วันที่แล้ว)<br/>
                                • ตรวจสอบ Processed Query ว่า WHERE condition ถูกต้องหรือไม่
                            </div>
                        </div>
                    `;
                    
                    frappe.msgprint({
                        title: __('🔍 Debug Query Information'),
                        message: html,
                        indicator: 'blue',
                        wide: true
                    });
                } else {
                    frappe.msgprint({
                        title: __('Debug ล้มเหลว'),
                        message: r.message.message,
                        indicator: 'red'
                    });
                }
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('เกิดข้อผิดพลาด'),
                message: __('ไม่สามารถดึงข้อมูล debug ได้'),
                indicator: 'red'
            });
        }
    });
}

function reset_last_sync(frm) {
    frappe.confirm(
        __('คุณต้องการ reset Last Sync เพื่อ sync ข้อมูลทั้งหมดใหม่หรือไม่?<br/><br/><strong>ตัวเลือก:</strong><br/>• <strong>Yes</strong> = ตั้งเป็น NULL (sync ทุกอย่าง)<br/>• <strong>No</strong> = ตั้งเป็น 1 สัปดาห์ที่แล้ว'),
        function() {
            // Reset เป็น NULL
            frm.set_value('last_sync', null);
            frm.save().then(() => {
                frappe.msgprint({
                    title: __('✅ Reset เสร็จสิ้น'),
                    message: __('Reset Last Sync เป็น NULL แล้ว - จะ sync ข้อมูลทั้งหมด'),
                    indicator: 'green'
                });
            });
        },
        function() {
            // ตั้งเป็น 1 สัปดาห์ที่แล้ว
            let one_week_ago = new Date();
            one_week_ago.setDate(one_week_ago.getDate() - 7);
            
            frm.set_value('last_sync', one_week_ago);
            frm.save().then(() => {
                frappe.msgprint({
                    title: __('✅ Reset เสร็จสิ้น'),
                    message: __(`ตั้ง Last Sync เป็น ${one_week_ago.toLocaleString()} แล้ว`),
                    indicator: 'green'
                });
            });
        }
    );
}

function test_ic360_connection(frm) {
    frappe.call({
        method: 'datahubv2.core.sd_incident.service.test_ic360_connection',
        freeze: true,
        freeze_message: __('🔗 กำลังทดสอบการเชื่อมต่อ IC360...<br/>กรุณารอสักครู่'),
        callback: function(r) {
            if (r.message) {
                if (r.message.success) {
                    let data = r.message.data;
                    
                    // สร้าง HTML สำหรับแสดงข้อมูล connection
                    let html = `
                        <div style="font-family: monospace;">
                            <h4>🔗 IC360 Connection Test</h4>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>✅ Status:</strong> <span style="color: green;">Connected Successfully</span>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>🏠 Host:</strong> <code>${data.host}</code>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>🗄️ Database:</strong> <code>${data.database}</code>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>👤 User:</strong> <code>${data.user}</code>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>🔌 Port:</strong> <code>${data.port}</code>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong>🧪 Test Query Result:</strong><br/>
                                <code>${JSON.stringify(data.test_query_result)}</code>
                            </div>
                            
                            <div style="padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">
                                <strong>✅ การเชื่อมต่อ IC360 ใช้งานได้ปกติ</strong><br/>
                                หากยังมีปัญหาการ sync ให้ตรวจสอบ SQL Query และ last_sync
                            </div>
                        </div>
                    `;
                    
                    frappe.msgprint({
                        title: __('🔗 IC360 Connection Test - Success'),
                        message: html,
                        indicator: 'green',
                        wide: true
                    });
                } else {
                    let data = r.message.data;
                    let connectionInfo = '';
                    
                    if (data) {
                        connectionInfo = `
                            <div style="margin-top: 15px;">
                                <strong>🔧 Connection Info:</strong><br/>
                                <code>Host: ${data.host}</code><br/>
                                <code>Database: ${data.database}</code><br/>
                                <code>User: ${data.user}</code><br/>
                                <code>Port: ${data.port}</code><br/>
                                <code>Status: ${data.connection_status}</code>
                            </div>
                        `;
                    }
                    
                    let html = `
                        <div style="font-family: monospace;">
                            <h4>❌ IC360 Connection Test Failed</h4>
                            
                            <div style="margin-bottom: 15px; color: red;">
                                <strong>Error:</strong> ${r.message.message}
                            </div>
                            
                            ${connectionInfo}
                            
                            <div style="padding: 10px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; margin-top: 15px;">
                                <strong>🔧 แนวทางแก้ไข:</strong><br/>
                                • ตรวจสอบ DH Setting ว่าข้อมูล IC360 connection ถูกต้องหรือไม่<br/>
                                • ตรวจสอบ network connectivity<br/>
                                • ตรวจสอบ database server status<br/>
                                • ตรวจสอบ user permissions
                            </div>
                        </div>
                    `;
                    
                    frappe.msgprint({
                        title: __('❌ IC360 Connection Test - Failed'),
                        message: html,
                        indicator: 'red',
                        wide: true
                    });
                }
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('เกิดข้อผิดพลาด'),
                message: __('ไม่สามารถทดสอบการเชื่อมต่อ IC360 ได้'),
                indicator: 'red'
            });
        }
    });
}

// Helper function สำหรับแสดงสถานะการทำงาน
frappe.ui.form.on('DH Incident API Config', {
    onload: function(frm) {
        // แสดงข้อมูล last sync ที่ชัดเจนขึ้น
        if (frm.doc.last_sync) {
            frm.set_df_property('last_sync', 'description', 
                `Last synced: ${moment(frm.doc.last_sync).format('DD/MM/YYYY HH:mm:ss')} (${moment(frm.doc.last_sync).fromNow()})`
            );
        }
    }
});
