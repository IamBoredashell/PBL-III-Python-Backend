import fastapi
import bcrypt
import jwt
import datetime
import psycopg
#local
import db
from schema import LoginResponse, LoginRequest
from config import JWTALGO, JWTSECRETKEY
router = fastapi.APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    print("Begining Login")

    async with db.getDictCursor() as cur:
        await cur.execute("SELECT * FROM user_account WHERE email = %s", (data.email,))
        row = await cur.fetchone()

        if row and row["status"]=="active":
            hash = row["hash"]
            user_id = row["id"]
            username = row["username"]
            user_role = row["user_role"]
            if bcrypt.checkpw(data.password.encode(), hash.encode()):
                expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=200)
                token = jwt.encode(
                    {"sub": str(user_id), "username": username,"role":user_role, "exp": expire},
                    JWTSECRETKEY,
                    algorithm=JWTALGO
                )
                print("Jwt assigned token:",token)
                return {"token": token}

    print("Invalid credentials")
    raise fastapi.HTTPException(status_code=401, detail="Invalid credentials")
