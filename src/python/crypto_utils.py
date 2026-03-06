from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import base64

class CryptoUtils:
    SALT_SIZE = 16
    KEY_SIZE = 32
    ITERATIONS = 100000

    @staticmethod
    def _get_key(password: str, salt: bytes) -> bytes:
        return PBKDF2(password, salt, dkLen=CryptoUtils.KEY_SIZE,
                      count=CryptoUtils.ITERATIONS, hmac_hash_module=SHA256)

    @staticmethod
    def encrypt(plaintext: str, master_password: str) -> str:
        salt = get_random_bytes(CryptoUtils.SALT_SIZE)
        key = CryptoUtils._get_key(master_password, salt)
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        combined = salt + cipher.nonce + tag + ciphertext
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_data: str, master_password: str) -> str:
        data = base64.b64decode(encrypted_data.encode('utf-8'))
        salt = data[:CryptoUtils.SALT_SIZE]
        nonce = data[CryptoUtils.SALT_SIZE:CryptoUtils.SALT_SIZE+16]
        tag = data[CryptoUtils.SALT_SIZE+16:CryptoUtils.SALT_SIZE+32]
        ciphertext = data[CryptoUtils.SALT_SIZE+32:]
        key = CryptoUtils._get_key(master_password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')

    @staticmethod
    def hash_master_password(password: str) -> str:
        salt = get_random_bytes(CryptoUtils.SALT_SIZE)
        key = CryptoUtils._get_key(password, salt)
        return base64.b64encode(salt + key).decode('utf-8')

    @staticmethod
    def verify_master_password(password: str, hashed: str) -> bool:
        data = base64.b64decode(hashed.encode('utf-8'))
        salt = data[:CryptoUtils.SALT_SIZE]
        expected_key = data[CryptoUtils.SALT_SIZE:]
        key = CryptoUtils._get_key(password, salt)
        return key == expected_key