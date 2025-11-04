import fastapi
import bcrypt
#local
import db
import auth
from schema import AddUserRequest, TokenPayload, userList, getUserListResponse, getChannelListResponse, getUserInfoAtChannel
router = fastapi.APIRouter()

@router.post("/admin/add_user")
async def add_user(
    user:AddUserRequest,
    payload:TokenPayload=fastapi.Depends(auth.verify_token)

):  
    print("JwtToken Payload:",payload)

    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)
    
    async with db.getDictCursor() as cur:
        await cur.execute("SELECT id FROM user_account WHERE email = %s or username = %s", (user.email, user.username))
        row = await cur.fetchone()
        if row:
            raise fastapi.HTTPException(status_code=403, detail="Email or username already exists")


    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()


    async with db.getDictCursor() as cur:

        try:
            # Insert into user_info first
            await cur.execute(
                "INSERT INTO user_info (first_name, last_name) VALUES (%s, %s) RETURNING id",
                (user.first_name, user.last_name)
            )

            print("Bruh")
            user_info_id = (await cur.fetchone())["id"]
            print("user_info_id =", user_info_id, type(user_info_id))
            # Then insert into user_account with foreign key
            await cur.execute(
                "INSERT INTO user_account (email, username, hash, user_role, status, user_info_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (user.email, user.username, hashed, user.role, "active", user_info_id)
            )
        except Exception as e:
            print("Error in db")
            return fastapi.responses.JSONResponse(
                content={"msg": f"DB error: {str(e)} {type(e)}"},
                status_code=500
            )

    return fastapi.responses.JSONResponse(
        content={"msg": f"user {user.username} created successfully"},
        status_code=200
    )
@router.post("/admin/add_channel")
@router.post("/admin/add_user_to_channel")
@router.post("/admin/delete_user_from_channel")
@router.post("admin/delete_channel")

@router.get("/admin/get_user_list", response_model=getUserListResponse)
async def get_user_list(
    payload:TokenPayload=fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)
    async with db.getDictCursor() as cur:
        try:
            await cur.execute('SELECT id, email, username, user_role, status FROM "user_account"')
            rows = await cur.fetchall()
        except Exception as e:
            print("Error in db:",e)
            return fastapi.responses.JSONResponse(
                content={"msg": f"DB error: {str(e)} {type(e)}"},
                status_code=500
            )
        return {"users":rows}
    

@router.get("/admin/get_channel_list", response_model=getChannelListResponse)
async def get_channel_list(
        payload:TokenPayload=fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)
    async with db.getDictCursor() as cur:
        try:
            await cur.execute('SELECT id, name,status FROM "channel"')
            rows = await cur.fetchall()
        except Exception as e:
            print("Error in db:",e)
            return fastapi.responses.JSONResponse(
                content={"msg": f"DB error: {str(e)} {type(e)}"},
                status_code=500
            )
        return {"channel":rows}

@router.get("/admin/get_userinfo_at_channel", response_model=getUserInfoAtChannel)
async def get_channel_list(
    payload: TokenPayload = fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)

    async with db.getDictCursor() as cur:
        try:
            await cur.execute("""
                SELECT 
                    c.id AS channel_id,
                    c.name AS channel_name,
                    u.id AS user_id,
                    u.username AS user_name,
                    cu.status,
                    cu.permission
                FROM channel_user cu
                JOIN channel c ON cu.channel_id = c.id
                JOIN user_account u ON cu.user_id = u.id
            """)
            rows = await cur.fetchall()
        except Exception as e:
            print("Error in db:", e)
            return fastapi.responses.JSONResponse(
                content={"msg": f"DB error: {str(e)} {type(e)}"},
                status_code=500
            )
        
        return {"UserInfo": rows}


@router.get("/admin/init_admin")
async def init_admin():
    print("Initializing admin")
    email = "admin@gmail.com"
    username = "admin"
    password = "admin@1234"
    user_role = "sys_admin"
    status="active"
    first_name="System"
    last_name="Admin"
    
    async with db.getDictCursor() as cur:
        # check if admin already exists
        await cur.execute("SELECT id FROM user_account WHERE username = %s", (username,))
        row = await cur.fetchone()
        
        if row:
            return fastapi.responses.JSONResponse(
                content={"msg": "Admin already exists"},
                status_code=200
            )

        # hash password with salt
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            # Insert into user_info first
            await cur.execute(
                "INSERT INTO user_info (first_name, last_name) VALUES (%s, %s) RETURNING id",
                (first_name, last_name)
            )

            user_info_id = (await cur.fetchone())["id"]
            print("user_info_id =", user_info_id, type(user_info_id))
            # Then insert into user_account with foreign key
            await cur.execute(
                "INSERT INTO user_account (email, username, hash, user_role, status, user_info_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (email, username, hashed, user_role, status, user_info_id)
            )
        except Exception as e:
            print("Error in db")
            return fastapi.responses.JSONResponse(
                content={"msg": f"DB error: {str(e)} {type(e)}"},
                status_code=500
            )

    return fastapi.responses.JSONResponse(
        content={"msg": "Admin user created successfully"},
        status_code=200
    )
