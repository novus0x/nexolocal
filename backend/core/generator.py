########## Modules ##########
import uuid, random, string, jwt, secrets, re

from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from core.config import settings

########## Variables ##########
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ALPHABET_PASSWORD = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%&*"
ENTITY_REGEX = re.compile(r"[^A-Z0-9]")
TOKEN_LENGTH = 12

########## Get uuid v4 - only value ##########
def get_uuid_value():
    uid = str(uuid.uuid4())
    
    return uid

########## Get uuid v4 ##########
def get_uuid(db: Session, model):
    uid = str(uuid.uuid4())

    while (1):
        if db.query(model).filter(model.id == uid).first():
            uid = str(uuid.uuid4())
        else: break
    
    return uid

########## Get short id ##########
async def get_short_id(db: Session, model):
    charset = string.ascii_letters + string.digits + "-_"
    short_id = ''.join(random.choices(charset, k=12))

    while (1):
        if db.query(model).filter(model.id == short_id).first():
            short_id = ''.join(random.choices(charset, k=12))
        else: break
    
    return short_id

########## Generate JWT ##########
def generate_jwt(session_id, expires):
    payload = {"session_id": session_id}

    if expires == "1":
        payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return encoded_jwt

########## Get NXID ##########
def generate_nxid(entity: str):
    entity = entity.upper()
    entity = ENTITY_REGEX.sub("", entity)
    entity = entity[:10] or "GEN"

    token = "".join(secrets.choice(ALPHABET) for _ in range(TOKEN_LENGTH))

    return f"NX-{entity}-{token[:4]}-{token[4:8]}-{token[8:]}"

########## Generate random password ##########
def generate_temp_password(length = TOKEN_LENGTH) -> str:
    password = "".join(secrets.choice(ALPHABET_PASSWORD) for _ in range(length))
    return password
