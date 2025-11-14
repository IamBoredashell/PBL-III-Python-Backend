import fastapi
import bcrypt
#local
import db
import auth
import webSockets
from schema import TokenPayload
from schemachat import MessageItem, ChannelItem, GetChannelsRequest, LoadMessagesRequest, MessageListResponse, ChannelListResponse , LoadUsersRequest, GetChannelsResponse, LoadUsersRequest, UserListResponse, UserItem



router = fastapi.APIRouter()
wsm=webSockets.ConnectionManager()


def has_perm(bits: int, n: int):
    return bool(bits & (1 << (n - 1)))

@router.websocket("/chats/{user_id}/ws")
async def chatSocket(websocket: fastapi.WebSocket, user_id: int, token: str):

    print("Beep boop")
    payload = await auth.verify_token_websocket(token)

    if int(payload["sub"]) != int(user_id):
        await websocket.close(code=4001)
        return

    await wsm.connect(user_id=user_id, websocket=websocket)

    try:
        while True:
            response = await websocket.receive_json()
            request = response.get("request")
            print(request)

            if not request:
                await websocket.send_json({"error": "missing request field"})

                continue

            # ====== GET CHANNELS ======
            if request == "get_channels":
                try:
                    data = GetChannelsRequest(**response)
                except Exception as e:
                    await websocket.send_json({"request": "get_channels", "error": str(e)})
                    continue

                result = await handle_get_channels(user_id, data)
                await websocket.send_json(result.model_dump())
                continue

            # ====== LOAD MESSAGES ======
            if request == "load_messages":
                try:
                    data = LoadMessagesRequest(**response)
                except Exception as e:
                    await websocket.send_json({"request": "load_messages", "error": str(e)})
                    continue

            # ====== LOAD USERS ======
            if request == "load_users":
                try:
                    data = LoadUsersRequest(**response)
                except Exception as e:
                    await websocket.send_json({"request": "load_users", "error": str(e)})
                    continue
                result = await handle_get_users(user_id,data)
                await websocket.send_json(result.model_dump())
                continue


            # ====== SEND MESSAGES ======
            if request == "send_message":
                try:
                    data = SendMessageRequest(**response)
                except Exception as e:
                    await websocket.send_json({"request": "send_message", "error": str(e)})
                    continue
                result = await handle_send_message(user_id,data)
                await websocket.send_json(result.model_dump())
                continue

            # ====== UNKNOWN ======
            await websocket.send_json({"error": f"Unknown request '{request}'"})

    except fastapi.WebSocketDisconnect:
        wsm.disconnect(user_id)


async def handle_load_messages(user_id: int, data: LoadMessagesRequest):
    channel_id = data.channel_id
    limit = data.limit or 1

    try:
        async with db.getDictCursor() as cur:

            # Check membership
            await cur.execute("""
                SELECT permission
                FROM channel_user
                WHERE user_id = %s AND channel_id = %s
            """, (user_id, channel_id))
            row = await cur.fetchone()

            if not row:
                return {"request": "load_messages", "error": "not_in_channel"}

            perm = row["permission"]

            if not has_perm(perm, 2):
                return {"request": "load_messages", "error": "no_read_permission"}

            # Load messages
            await cur.execute("""
                SELECT 
                    m.id AS message_id,
                    m.sender AS sender_id,
                    m.timestamp,
                    m.message,
                    m.status,
                    u.username AS sender_name
                FROM message m
                JOIN user_account u ON u.id = m.sender
                WHERE m.channel_id = %s
                ORDER BY m.timestamp DESC
                LIMIT %s
            """, (channel_id, limit))

            rows = await cur.fetchall()

            if not rows:
                return {"request": "load_messages", "messages": []}

            result = []
            for r in rows:
                st = r["status"]

                if st == "Deleted" and not has_perm(perm, 7):
                    continue
                if st == "Edited" and not has_perm(perm, 8):
                    continue

                result.append(MessageItem(
                    channel_id=channel_id,
                    message_id=r["message_id"],
                    sender_id=r["sender_id"],
                    sender_name=r["sender_name"],
                    message=r["message"],
                    timestamp=str(r["timestamp"]),
                    status=st
                ))

            return MessageListResponse(messages=result)

    except Exception as e:
        return {
            "request": "load_messages",
            "error": "internal_error",
            "detail": str(e)
        }



async def handle_get_channels(user_id: int, data: GetChannelsRequest):

    try:
        async with db.getDictCursor() as cur:

            # Get all channels user is in
            await cur.execute("""
                SELECT channel_id, permission
                FROM channel_user
                WHERE user_id = %s
            """, (user_id,))
            
            rows = await cur.fetchall()
            channels = []

            for row in rows:
                channel_id = row["channel_id"]
                perm = row["permission"]

                # ---- Fetch channel name ----
                await cur.execute("""
                    SELECT name 
                    FROM channel
                    WHERE id = %s
                """, (channel_id,))
                ch = await cur.fetchone()

                channel_name = ch["name"] if ch else "Unknown"

                # ---- Fetch last message ----
                last_msg = None

                if has_perm(perm, 2): 
                    res = await handle_load_messages(
                        user_id,
                        LoadMessagesRequest(
                            request="load_messages",
                            channel_id=channel_id,
                            limit=1
                        )
                    )
                    if res.get("messages"):
                        last_msg = res["messages"][0]

                channels.append({
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "last_message": last_msg
                })

            return GetChannelsResponse(channels=channels)

    except Exception as e:
        return {"request": "get_channels", "error": "internal_error", "detail": str(e)}



async def handle_get_users(user_id: int, data: LoadUsersRequest):
    channel_id = data.channel_id

    try:
        async with db.getDictCursor() as cur:

            await cur.execute("""
                SELECT permission
                FROM channel_user
                WHERE user_id = %s AND channel_id = %s
            """, (user_id, channel_id))
            row = await cur.fetchone()

            if not row:
                return {"type": "user_list", "error": "not_in_channel"}

            perm = row["permission"]

            if not has_perm(perm, 2):
                return {"type": "user_list", "error": "no_read_permission"}

            await cur.execute("""
                SELECT 
                    u.id AS user_id,
                    u.username AS user_name
                    cu.permission AS permission
                FROM channel_user cu
                JOIN user_account u ON u.id = cu.user_id
                WHERE cu.channel_id = %s
            """, (channel_id,))
            
            rows = await cur.fetchall()

            users = [
                UserItem(
                    user_id=r["user_id"],
                    user_name=r["user_name"],
                    permission=r["permission"]
                )
                for r in rows
            ]

            return UserListResponse(users=users)

    except Exception as e:
        return {
            "type": "user_list",
            "error": "internal_error",
            "detail": str(e)
        }



async def handle_messages(user_id: int, data: SendMessageRequest):
    channel_id = data.channel_id
    status = data.status      # "Normal", "Edited", "Deleted", "Attachment"
    message = data.message
    prev_id = data.prev_id if hasattr(data, "prev_id") else None

    try:
        async with db.getDictCursor() as cur:

            # 1. Check permissions
            await cur.execute("""
                SELECT permission
                FROM channel_user
                WHERE user_id = %s AND channel_id = %s
            """, (user_id, channel_id))
            row = await cur.fetchone()

            if not row:
                return {"type": "send_message", "error": "not_in_channel"}

            perm = row["permission"]

            required = [3, 4, 5, 6, 9]   # same bits you defined

            for bit in required:
                if not has_perm(perm, bit):
                    return {"type": "send_message", "error": f"missing_perm_{bit}"}

            # 2. Insert new message entry
            await cur.execute("""
                INSERT INTO message (channel_id, sender, message, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id, timestamp
            """, (channel_id, user_id, message, status))

            saved = await cur.fetchone()

            msg_id = saved["id"]
            timestamp = saved["timestamp"]

    except Exception as e:
        return {
            "type": "send_message",
            "error": "internal_error",
            "detail": str(e)
        }

    # 3. Dispatch
    if status == "Normal":
        return await handle_message_normal(user_id, channel_id, msg_id)

    if status == "Edited":
        return await handle_message_edited(user_id, channel_id, msg_id, prev_id)

    if status == "Deleted":
        return await handle_message_deleted(user_id, channel_id, msg_id, prev_id)

    if status == "Attachment":
        return await handle_message_attachment(user_id, channel_id, msg_id)

    return {"type": "send_message", "error": "unknown_status"}




async def handle_message_normal(user_id: int, channel_id: int, msg_id: int):
    try:
        async with db.getDictCursor() as cur:
            await cur.execute("""
                SELECT id
                FROM channel_user
                WHERE channel_id = %s
            """, (channel_id,))
            rows = await cur.fetchall()

        for row in rows:
            uid = row["id"]
            await webSockets.send_to_user(uid, {
                "type": "new_message",
                "channel_id": channel_id,
                "message_id": msg_id
            })

        return {"type": "send_message", "status": "success", "id": msg_id}

    except Exception as e:
        return {"type": "send_message", "error": "normal_failed", "detail": str(e)}


async def handle_message_edited(user_id: int, channel_id: int, msg_id: int, prev_id: int):
    try:
        async with db.getDictCursor() as cur:
            await cur.execute("""
                UPDATE message
                SET status = 'Edited'
                WHERE id = %s AND channel_id = %s
            """, (prev_id, channel_id))

            await cur.execute("""
                UPDATE message
                SET status = 'Edit'
                WHERE id = %s AND channel_id = %s
            """, (msg_id, channel_id))

            await cur.execute("""
                SELECT id
                FROM channel_user
                WHERE channel_id = %s
            """, (channel_id,))
            rows = await cur.fetchall()

        for row in rows:
            uid = row["id"]
            await webSockets.send_to_user(uid, {
                "type": "edit_message",
                "channel_id": channel_id,
                "prev_id": prev_id,
                "new_id": msg_id
            })

        return {"type": "send_message", "status": "edited", "id": msg_id}

    except Exception as e:
        return {"type": "send_message", "error": "edit_failed", "detail": str(e)}



async def handle_message_deleted(user_id: int, channel_id: int, msg_id: int, prev_id: int):
    try:
        async with db.getDictCursor() as cur:
            await cur.execute("""
                UPDATE message
                SET status = 'Deleted'
                WHERE id = %s AND channel_id = %s
            """, (prev_id, channel_id))

            await cur.execute("""
                UPDATE message
                SET status = 'Delete'
                WHERE id = %s AND channel_id = %s
            """, (msg_id, channel_id))

            await cur.execute("""
                SELECT id
                FROM channel_user
                WHERE channel_id = %s
            """, (channel_id,))
            rows = await cur.fetchall()

        for row in rows:
            uid = row["id"]
            await webSockets.send_to_user(uid, {
                "type": "delete_message",
                "channel_id": channel_id,
                "prev_id": prev_id,
                "new_id": msg_id
            })

        return {"type": "send_message", "status": "deleted", "id": msg_id}

    except Exception as e:
        return {"type": "send_message", "error": "delete_failed", "detail": str(e)}


