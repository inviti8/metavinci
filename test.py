from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key = private_key.public_key()

print(public_key.exportKey().decode('utf-8'))
#print(private_key.exportKey().decode('utf-8'))