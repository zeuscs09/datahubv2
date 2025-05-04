import random
from datetime import datetime

class Helper:
    def __init__(self):
        pass

    def generate_code(self, total_length=14):
        now = datetime.now()
        prefix = now.strftime('%Y%m')  # MMYYYY = 6 characters
        prefix = prefix +"9"
        remaining_length = total_length - len(prefix)
        if remaining_length <= 0:
            raise ValueError("Total length must be greater than 6 (MMYYYY length)")

        # แบ่งความยาวระหว่าง micro_part และ random_part (ครึ่งๆ)
        micro_len = remaining_length // 2
        rand_len = remaining_length - micro_len  # เผื่อกรณีเลขคี่

        micro_part = now.strftime('%f')[:micro_len]  # จาก microsecond
        max_rand = 10 ** rand_len - 1
        random_part = f"{random.randint(0, max_rand):0{rand_len}d}"

        return f"{prefix}{micro_part}{random_part}"
    
