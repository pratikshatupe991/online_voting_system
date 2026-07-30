from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """
    Hashes a plain-text password using a secure algorithm (default is scrypt).
    """
    return generate_password_hash(password)


def verify_password(password_hash, password):
    """
    Checks a plain-text password against the stored hash.
    Returns True if they match, False otherwise.
    """
    return check_password_hash(password_hash, password)
