from cryptography.fernet import Fernet
import os

# FIXED KEY: We use this exact string so restarts don't break encryption.
# In a real startup, put this in your .env file.
FIXED_KEY = "k4v7hLpQ9n3xR8zW1yM2oJ5tB6gV0cE3dF9aU8sI7rX=" 

# Use the fixed key, or fetch from env if you added it there
KEY = os.getenv("ENCRYPTION_KEY", FIXED_KEY)
cipher = Fernet(KEY)

def encrypt_data(data: str) -> str:
    """Scramble text so it looks like garbage in the DB."""
    if not data: return ""
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    """Unscramble text back to readable English."""
    if not token: return ""
    return cipher.decrypt(token.encode()).decode()