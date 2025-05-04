import logging
import frappe

def get_logger(name):
    """Get a logger that logs to frappe's error log"""
    
    class FrappeLogHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            frappe.log_error(message=msg, title=f"{name} - {record.levelname}")
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # เพิ่ม handler สำหรับเขียนลง frappe log
    handler = FrappeLogHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # ลบ handler เดิมที่อาจมีอยู่
    for hdlr in logger.handlers[:]:
        logger.removeHandler(hdlr)
    
    logger.addHandler(handler)
    
    return logger 