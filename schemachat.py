from pydantic import BaseModel
from typing import Optional, Literal, List


# ===== Items =====
class MessageItem(BaseModel):
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    status: Optional[str] = None

class ChannelItem(BaseModel):
    channel_id: int
    channel_name: str
    last_message: Optional[MessageItem] = None

class UserItem(BaseModel):
    user_id: int
    user_name: str
    permission: int

# ===== Requests =====
class BaseRequest(BaseModel):
    request: str

class GetUsersRequest(BaseRequest):
    request: Literal["get_users"]

class GetChannelsRequest(BaseRequest):
    request: Literal["get_channels"]
    last_channel_id: Optional[int] = None
    limit: int = 1

class LoadMessagesRequest(BaseRequest):
    request: Literal["load_messages"]
    channel_id: int
    limit: int = 1


class LoadUsersRequest(BaseRequest):
    request: Literal["load_users"]
    channel_id: int

# ===== Responses =====


class GetChannelsResponse(BaseModel):
    request: Literal["get_channels"] = "get_channels"
    channels: Optional[List[ChannelItem]] = None


class UserListResponse(BaseModel):
    request: Literal["get_users"] = "get_users"
    users: List[UserItem]


class ChannelListResponse(BaseModel):
    request: Literal["get_channels"] = "get_channels"
    channels: List[ChannelItem]


class MessageListResponse(BaseModel):
    request: Literal["load_messages"] = "load_messages"
    messages: List[MessageItem]
