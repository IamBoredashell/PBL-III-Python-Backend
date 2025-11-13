import fastapi
import bcrypt
#local
import db
import auth
import webSockets
from schema import 

router = fastapi.APIRouter()
wsm=webSockets.ConnectionManager()

@router.websocket("/chats/{user_id}")
async def chatSocket(websocket:fastapi.WebSocket,user_id:int,token:str):
    print("Trying to Connect with user",user_id)
    payload=await auth.verify_token_websocket(token)
    print("Token Verified")
    if int(payload["sub"])!=int(user_id):
        await websocket.close(code=4001)
        return
    await wsm.connect(user_id=user_id,websocket=websocket)
    print("User ID: ",user_id," Connected to chat")
    try:
        while True:
            response = await websocket.receive_json()

    except fastapi.WebSocketDisconnect:
        wsm.disconnect(user_id)
        print("User ID: ",user_id," Disconnected from chat")

async def get_channels(number:int):
    async with db.getDictCur() as cur:
        try:
            await cur.execute()
    return x

