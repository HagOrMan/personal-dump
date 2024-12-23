"""

Example usage:

- Encrypt a file in a different folder
    `python encrypt_files.py -e -f ../raw-thoughts/MyFile.md -k MySuperUnhackableKey -n ../raw-thoughts/MyFile_encrypt.md`

    - Make sure the file can be decrypted
        `python encrypt_files.py -f ../raw-thoughts/MyFile_encrypt.md -k MySuperUnhackableKey`
"""

import argparse
from cryptography.fernet import Fernet
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Encrypt and decrypt files to store them remotely in a secure manner")
    parser.add_argument("-e", "--encrypt", action="store_true", help="(optional) If the program should encrypt the file. If not provided, the file will be decrypted.")
    parser.add_argument("-f", "--file", type=str, required=True, help="Path to file to encrypt / decrpyt")
    parser.add_argument("-k", "--key", type=str, required=True, help="Value of key to use for encrypting / decrypting")
    parser.add_argument("-n", "--new-file", type=str, help="(optional) If provided, the encryption / decryption output will be saved into a file of this path.")
    parser.add_argument("-o", "--overwrite-new-file", action="store_true", help="(optional) If provided, the new file will overwrite an existing file. If not provided, and the new file already exists at that path, the program will throw an error.")
    return parser.parse_args()

def encrypt_string(string_to_encrypt: str, key: str):
    try:
        f = Fernet(key)
        return f.encrypt(string_to_encrypt.encode('utf-8')).decode('utf-8') # Decodes it as well so we can view it as a string (easier to save in files).
    except BaseException as e:
        e.add_note("Failed to encrypt file. Check if the key you are using is valid. You may need to generate a new one.")
        raise e

def decrypt_string(string_to_decrypt: str, key: str):
    try:
        f = Fernet(key)
        return f.decrypt(string_to_decrypt).decode('utf-8')
    except BaseException as e:
        e.add_note("Failed to decrypt file. Check that the path is pointing to an encrypted file. If you are decrypting a file that has not been encrypted, it will fail. Also check that your key is correct.")
        raise e

def read_file(file_path: os.PathLike) -> str:
    with open(file_path, mode='r') as file:
        file_content = file.read()

    return file_content

def save_to_file(file_path: os.PathLike, content: str):
    with open(file_path, mode='w') as file:
        file.write(content)

def safety_checks(file: os.PathLike, new_file: os.PathLike, overwrite_new_file: bool):
    """Checks any and all content that could pose an issue before running the program."""
    if not os.path.exists(file):
        raise ValueError("The path where the file is being read from must exist.")
    
    if os.path.isdir(file):
        raise ValueError("The file to read from must point towards a file. It currently points towards a directory.")

    if new_file:
        if os.path.isdir(new_file):
            raise ValueError("The file to save to must point towards a file. It currently points towards a directory.")
        
        if os.path.exists(new_file) and not overwrite_new_file:
            raise ValueError("The file to save to already exists. Must be a non-existent file. Run this program with `-o` to ignore this warning.")

def main():
    args = parse_args()
    encrypt: bool = args.encrypt
    file: str = args.file
    key: str = args.key
    new_file: str = args.new_file
    overwrite_new_file: bool = args.overwrite_new_file

    safety_checks(file, new_file, overwrite_new_file)
    
    file_content = read_file(file)

    token = encrypt_string(file_content, key) if encrypt else decrypt_string(file_content, key)

    # Either saves it into a new file or prints it.
    if new_file:
        save_to_file(new_file, token)
    else:
        print(token)

if __name__ == '__main__':
    main()
