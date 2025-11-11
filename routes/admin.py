import fastapi
import bcrypt
#local
import db
import auth
from schema import AddUserRequest, TokenPayload, userList, getUserListResponse, getChannelListResponse, getUserInfoAtChannel, AddChannelRequest, EditUserRequest, EditUserChannelRequest, DeleteChannelRequest
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
            await cur.execute(
                "INSERT INTO user_info (first_name, last_name) VALUES (%s, %s) RETURNING id",
                (user.first_name, user.last_name)
            )

            user_info_id = (await cur.fetchone())["id"]
            print("user_info_id =", user_info_id, type(user_info_id))
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

@router.post("/admin/edit_user")
async def edit_user(
    info: EditUserRequest,
    payload: TokenPayload = fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)

    async with db.getDictCursor() as cur:
        await cur.execute('SELECT * FROM "user_account" WHERE id = %s', (info.user_id,))
        user = await cur.fetchone()
        if not user:
            raise fastapi.HTTPException(status_code=404, detail="User not found")

        await cur.execute(
            'UPDATE "user_account" SET email = %s, username = %s, user_role = %s, status = %s WHERE id = %s',
            (info.email, info.username, info.user_role, info.status, info.user_id)
        )

        if info.first_name or info.last_name:
            await cur.execute('SELECT user_info_id FROM "user_account" WHERE id = %s', (info.user_id,))
            user_info = await cur.fetchone()
            if user_info and user_info["user_info_id"]:
                await cur.execute(
                    'UPDATE "user_info" SET first_name = %s, last_name = %s WHERE id = %s',
                    (info.first_name, info.last_name, user_info["user_info_id"])
                )

        return fastapi.responses.JSONResponse(
            content={"msg": f"user {info.username} edited successfully"},
            status_code=200
        )

@router.post("/admin/add_channel")
async def add_channel(
    channel: AddChannelRequest,
    payload: TokenPayload = fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)

    async with db.getDictCursor() as cur:
        await cur.execute("SELECT name FROM channel WHERE name = %s", (channel.name,))
        row = await cur.fetchone()
        if row:
            raise fastapi.HTTPException(status_code=403, detail="Channel Name already exists")

    async with db.getDictCursor() as cur:
        try:
            await cur.execute(
                "INSERT INTO channel (name, status) VALUES (%s, %s)",
                (channel.name, channel.status)
            )
        except Exception as e:
            print("Error in db:", e)
            return fastapi.responses.JSONResponse(
                content={"msg": f"DB error: {str(e)}"},
                status_code=500
            )

    return fastapi.responses.JSONResponse(
        content={"msg": f"Channel {channel.name} created successfully"},
        status_code=200
    )

@router.post("/admin/delete_channel")
async def delete_channel(
    info: DeleteChannelRequest,
    payload: TokenPayload = fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)
    async with db.getDictCursor() as cur:
        await cur.execute(
            'UPDATE "channel" SET status = %s WHERE id = %s',
            ("deleted", info.channel_id)
        )
        return fastapi.responses.JSONResponse(
            content={"msg":f"Channel {info.name} Deleted successfully"},
            status_code=200
        )

@router.post("/admin/edit_user_channel")
async def edit_user_channel(
    info:  EditUserChannelRequest,
    payload: TokenPayload = fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)

    async with db.getDictCursor() as cur:
        # check channel status
        await cur.execute('SELECT status FROM "channel" WHERE id = %s', (info.channel_id,))
        row = await cur.fetchone()
        if not row or row["status"] != "active":
            raise fastapi.HTTPException(status_code=403, detail="Check channel status")

        await cur.execute('SELECT status FROM "user_account" WHERE id = %s', (info.user_id,))
        row = await cur.fetchone()
        if not row or row["status"] != "active":
            raise fastapi.HTTPException(status_code=403, detail="Check user status")

        await cur.execute('SELECT * FROM "channel_user" WHERE channel_id = %s AND user_id = %s', (info.channel_id, info.user_id))
        row = await cur.fetchone()

        if row:
            await cur.execute(
                'UPDATE "channel_user" SET permission = %s, status = %s WHERE channel_id = %s AND user_id = %s',
                (info.permission, info.status, info.channel_id, info.user_id)
            )
        else:
            await cur.execute(
                'INSERT INTO "channel_user" (channel_id, user_id, permission, status) VALUES (%s, %s, %s, %s)',
                (info.channel_id, info.user_id, info.permission, info.status)
            )

        return fastapi.responses.JSONResponse(
            content={"msg":f"Updated User Channel relation"},
            status_code=200
        )

@router.get("/admin/get_user_list", response_model=getUserListResponse)
async def get_user_list(
    payload:TokenPayload=fastapi.Depends(auth.verify_token)
):
    if payload["role"] != "sys_admin":
        raise fastapi.HTTPException(status_code=401)
    async with db.getDictCursor() as cur:
        try:
            await cur.execute("""
                SELECT
                    a.id AS id,
                    a.username as username,
                    a.email as email,
                    a.status as status,
                    a.user_role as user_role,
                    i.first_name as first_name,
                    i.last_name as last_name
                FROM user_account a 
                JOIN user_info i ON a.user_info_id = i.id
            """)
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
                    u.username AS username,
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
