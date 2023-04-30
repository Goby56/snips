import datetime
import jwt, bcrypt

def generate_token(username: str, secret_key: str):
    payload = {
        "user": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
    }
    return jwt.encode(payload, secret_key)

def validate_token(token: str, secret_key: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.exceptions.ExpiredSignatureError:
        return False
    return payload

def get_session(request, secret_key: str):
    token = request.cookies.get("token")
    if not token:
        return {"authorized": False}
    payload = validate_token(token, secret_key)
    if not payload:
        return {"authorized": False}
    return payload | {"authorized": True}

def hash_password(password: str):
    salt = bcrypt.gensalt()
    hashed_pass_encoded_salt = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_pass_encoded_salt.decode("utf-8")

def verify_password(pw: str, hashed_pw: bytearray):
    return bcrypt.checkpw(pw.encode("utf-8"), bytes(hashed_pw))
