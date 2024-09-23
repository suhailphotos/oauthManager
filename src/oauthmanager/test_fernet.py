from cryptography.fernet import Fernet

encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)
encrpyted_value = cipher_suite.encrypt(b'Hello World')
print("Encripted value: ", encrpyted_value)

# encrpted value = b'gAAAAABm8ci_x6lC6G1oZXhHDo4LO2yVyec9NnwFkVA7g-OUDTGcFgGEa0-qDG6SIUsqQnmpageEq-bQS6Rvg43pLNuncj80JQ=='

print("Encripted value: ", encrpyted_value.decode())

decrypted_value = cipher_suite.decrypt(encrpyted_value)

print("Decripted value: ", decrypted_value)


