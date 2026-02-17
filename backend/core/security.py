########## Modules ##########
import jwt, bcrypt, base64

from core.config import settings

########## Hash password ##########
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed_password.decode("utf-8")

########## Check password ##########
def check_password(encrypted_password, password):
    return bcrypt.checkpw(password.encode("utf-8"), encrypted_password.encode("utf-8"))

########## Check JWT ##########
def check_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None, True

    return payload, None

########## Generate base64 file ##########
def generate_base_64(data):
    base64_str = base64.b64encode(data) # data --> bytes

    return base64_str

########## Decode base64 file ##########
def decode_base_64(data):
    original_str = base64.b64decode(data) # data --> bytes/str

    return original_str
