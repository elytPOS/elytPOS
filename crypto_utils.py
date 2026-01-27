import os
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"


def load_key():
    """
    Load the existing key from the current directory or generate a new one.
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key


def encrypt_file(file_path):
    """
    Encrypts the file at file_path and saves it as file_path + '.enc'.
    Removes the original file.
    """
    if not os.path.exists(file_path):
        return

    key = load_key()
    f = Fernet(key)

    with open(file_path, "rb") as file:
        file_data = file.read()

    encrypted_data = f.encrypt(file_data)

    with open(file_path + ".enc", "wb") as file:
        file.write(encrypted_data)

    os.remove(file_path)


def decrypt_content(enc_file_path):
    """
    Reads an encrypted file and returns the decrypted content as a string.
    """
    key = load_key()
    f = Fernet(key)

    with open(enc_file_path, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data.decode("utf-8")
