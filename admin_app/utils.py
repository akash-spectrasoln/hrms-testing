from datetime import timedelta, date

def calculate_leave_days(start_date, end_date, holidays, floating_holidays):
    total_days = (end_date - start_date).days + 1  # Including both start and end date
    leave_days = total_days

    # Print out initial values for debugging
    print(f"Total days: {total_days}")
    print(f"Holidays: {holidays}")
    print(f"Floating Holidays: {floating_holidays}")

    # Convert holidays and floating holidays to datetime.date if not already
    holidays = [holiday if isinstance(holiday, date) else date(holiday.year, holiday.month, holiday.day) for holiday in holidays]
    floating_holidays = [floating_holiday if isinstance(floating_holiday, date) else date(floating_holiday.year, floating_holiday.month, floating_holiday.day) for floating_holiday in floating_holidays]

    # Loop over the date range and exclude weekends and holidays
    current_date = start_date
    while current_date <= end_date:
        print(f"Checking date: {current_date}")

        # Exclude weekends (Saturday and Sunday)
        if current_date.weekday() in [5, 6]:  # 5 = Saturday, 6 = Sunday
            leave_days -= 1
            print(f"Excluded weekend: {current_date}")

        # Exclude holidays
        elif current_date in holidays:
            leave_days -= 1
            print(f"Excluded holiday: {current_date}")

        # Exclude floating holidays
        elif current_date in floating_holidays:
            leave_days -= 1
            print(f"Excluded floating holiday: {current_date}")

        # Move to the next day
        current_date += timedelta(days=1)

    print(f"Final leave days: {leave_days}")
    return leave_days


import os
import json
import base64
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag, InvalidKey

def derive_employee_key(employee_id: str, created_on, salt: bytes, iterations: int = 100000) -> bytes:
    """Derive a unique key per employee from employee_id and created_on.day."""
    try:
        create_day = created_on.day if hasattr(created_on, 'day') else 1
        try:
            emp_int = int(employee_id)
        except Exception:
            emp_int = abs(hash(employee_id)) % (10 ** 8)
        secret_base = emp_int + create_day
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        key = kdf.derive(str(secret_base).encode())
        return key
    except Exception as e:
        raise ValueError(f"Key derivation failed: {e}")

def encrypt_employee_field(data, employee_id, created_on, iterations=100000):
    original_type = type(data).__name__
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_employee_key(employee_id, created_on, salt, iterations)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(str(data).encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    enc_data = encryptor.update(padded) + encryptor.finalize()
    result = [
        base64.b64encode(enc_data).decode(),
        base64.b64encode(nonce).decode(),
        base64.b64encode(encryptor.tag).decode(),
        base64.b64encode(salt).decode(),
        original_type,
        iterations,
    ]
    return json.dumps(result)

def decrypt_employee_field(enc_value, employee_id, created_on, iterations=100000):
    if not enc_value:
        return None
    try:
        enc_value = json.loads(enc_value)
        enc_data, nonce, tag, salt, original_type, iterations = enc_value
        salt = base64.b64decode(salt)
        key = derive_employee_key(employee_id, created_on, salt, iterations)
        nonce = base64.b64decode(nonce)
        tag = base64.b64decode(tag)
        enc_data = base64.b64decode(enc_data)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(enc_data) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded) + unpadder.finalize()
        if original_type == "str":
            return data.decode("utf-8")
        elif original_type == "int":
            return int(data.decode("utf-8"))
        elif original_type == "float":
            return float(data.decode("utf-8"))
        else:
            return data.decode("utf-8")
    except Exception as e:
        print(f"Decryption error: {e}")
        return None