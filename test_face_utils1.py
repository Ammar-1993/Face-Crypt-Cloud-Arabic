from utils import face_utils

def test_encrypt_decrypt():
    sample = [0.123456789, -0.23456789, 0.3456789]
    encrypted = face_utils.encrypt_encoding(sample)
    print("Encrypted:", encrypted)
    decrypted = face_utils.decrypt_encoding(encrypted)
    print("Decrypted:", decrypted)
    assert sample == decrypted
    print("✅ Test Passed")

if __name__ == "__main__":
    test_encrypt_decrypt()
