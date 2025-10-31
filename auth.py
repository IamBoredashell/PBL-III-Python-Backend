import fastapi
import jwt

# local
from config import JWTSECRETKEY, JWTALGO

security = fastapi.security.HTTPBearer()

async def verify_token(credentials: fastapi.Depends = fastapi.Depends(security)):
    print("Token received:", credentials)
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            JWTSECRETKEY,
            algorithms=[JWTALGO]
        )
        print("Decoded payload:", payload)
        return payload
    except jwt.ExpiredSignatureError as e:
        print("Jwt Error:",e)
        raise fastapi.HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        print("Jwt Error:",e)
        raise fastapi.HTTPException(status_code=401, detail="Invalid token")


async def verify_token_websocket(token:str):
    try:
        payload=jwt.decode(token,JWTSECRETKEY,algorithms=[JWTALGO])
        return payload
    except jwt.ExpiredSignatureError as e:
        print("Jwt Error:",e)
        raise fastapi.HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        print("Jwt Error:",e)
        raise fastapi.HTTPException(status_code=401, detail="Invalid token")

