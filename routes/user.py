import fastapi
import json
#local
import db
import auth 
import webSockets
from schema import UserInfoResponse
router = fastapi.APIRouter()
wsm = webSockets.ConnectionManager()


@router.get("/user")
async def hello(
        payload: dict = fastapi.Depends(auth.verify_token)
):
    print("User Connected successfully")
    return {"msg": f"Hello {payload.get('username', 'user')}!"}

@router.get("/user/{user_id}/info",response_model=UserInfoResponse)
async def get_user(
        user_id: int,
        payload: dict=fastapi.Depends(auth.verify_token)
    ):
    requester_id=int(payload["sub"])
    role=payload["role"]
    if requester_id!=user_id and role != "sys_admin":
        raise fastapi.HTTPException(status_code=403,detail="Forbidden")

    async with db.getDictCursor() as cur:
        await cur.execute(
            """
            SELECT ua.email, ua.username, ua.user_role, ui.first_name, ui.last_name
            FROM user_account ua
            JOIN user_info ui ON ua.user_info_id = ui.id
            WHERE ua.id = %s
            """,
            (user_id,)
        )
        row = await cur.fetchone()
    
    if not row:
        raise fastapi.HTTPException(status_code=404,detail="User not found")
    return UserInfoResponse(
        email=row["email"],
        username=row["username"],
        role=row["user_role"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or ""
    )



#Test Routes 

@router.websocket("/user/{user_id}/websocketTest2")
async def websocketTest(websocket: fastapi.WebSocket, user_id:int):
    token = websocket.headers.get("Authorization")
    payload= await auth.verify_token_websocket(token)
    print("token verified")
    if int(payload["sub"])!=int(user_id):
        await websocket.close(code=4001)
        return
    
    await wsm.connect(user_id=user_id,websocket=websocket)

    try:
        while True:
            data=await websocket.receive_text()
            await wsm.send_to_user(user_id,f"User {user_id} says:{data}")

    except fastapi.WebSocketDisconnect:
        wsm.disconnect(user_id)


@router.websocket("/user/{user_id}/websocketTest")
async def websocketTest(websocket: fastapi.WebSocket, user_id:int, token:str):
    print("Before token verify")
    print(token)
    payload= await auth.verify_token_websocket(token)
    print("token verified")
    if int(payload["sub"])!=int(user_id):
        await websocket.close(code=4001)
        return
    
    await wsm.connect(user_id=user_id,websocket=websocket)

    try:
        while True:
            response = await websocket.receive_json()
            await wsm.broadcast(user_id, response["text"])

    except fastapi.WebSocketDisconnect:
        wsm.disconnect(user_id)


