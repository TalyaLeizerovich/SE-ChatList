from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

ENCRYPTION_SALT = b'TalyaProject2025SecureSalt9876!'
ENCRYPTION_PASSWORD = "MySuper$ecureP@ssw0rd!2025"

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

ENCRYPTION_KEY = generate_key_from_password(ENCRYPTION_PASSWORD, ENCRYPTION_SALT)
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_text(plain_text: str) -> str:
    if plain_text is None or plain_text == "":
        return plain_text
    
    try:
        encrypted_bytes = cipher_suite.encrypt(plain_text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Error encrypting text: {e}")
        return plain_text

def decrypt_text(encrypted_text: str) -> str:
    if encrypted_text is None or encrypted_text == "":
        return encrypted_text
    
    try:
        decrypted_bytes = cipher_suite.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting text: {e}")
        return encrypted_text