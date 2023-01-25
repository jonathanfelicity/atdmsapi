import hashlib



def generate_password_hash(password: str) -> str:
    # Create a new sha256 hash object
    sha256 = hashlib.sha256()

    # Hash the password
    sha256.update(password.encode())

    # Return the hexadecimal representation of the hashed password
    return sha256.hexdigest()



def check_password_hash(hashed_password: str, password: str) -> bool:
    # Create a new sha256 hash object
    sha256 = hashlib.sha256()

    # Hash the given password
    sha256.update(password.encode())

    # Compare the given password hash with the stored password hash
    return sha256.hexdigest() == hashed_password
