import datetime, string, random, urllib, json
import jwt, bcrypt

def generate_token(secret_key: str, invalid: bool = False, **kwargs):
    payload = {
        # "username": username,
        # "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15) * (-1)**invalid
    }
    return jwt.encode(payload | kwargs, secret_key)

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

def generate_post_suffix():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def str2url(text: str):
    return urllib.parse.quote(text.strip().replace(" ", "-"))

def sql_result_to_dict(result: list, columns: dict):
    return [{k: p[i] for i, k in enumerate(["id"] + list(columns.keys()))} for p in result]
