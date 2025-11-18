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
    prev_id: Optional[int] = None

class ChannelItem(BaseModel):
    channel_id: int
    channel_name: str
    last_message: Optional[MessageItem] = None
    permission: Optional[int] = None

class UserItem(BaseModel):
    user_id: int
    user_name: str
    permission: int
    #weird fix for emergency
    channel_id: int

# ===== Requests =====
class BaseRequest(BaseModel):
    request: str


class GetChannelsRequest(BaseRequest):
    request: Literal["get_channels"]
    last_channel_id: Optional[int] = None
    limit: int = 1

class LoadMessagesRequest(BaseRequest):
    request: Literal["load_messages"]
    channel_id: int
    limit: int = 1
    prev_id: Optional[int] = None


class LoadUsersRequest(BaseRequest):
    request: Literal["load_users"]
    channel_id: int

class SendMessageRequest(BaseRequest):
    request: Literal["send_message"]
    channel_id: int
    status: Literal["Normal","Edited","Deleted","Attachment"]
    message: Optional[str]= None
    prev_id: Optional[int] = None


# ===== Responses =====


class GetChannelsResponse(BaseModel):
    request: Literal["get_channels"] = "get_channels"
    channels: Optional[List[ChannelItem]] = None


class UserListResponse(BaseModel):
    request: Literal["load_users"] = "load_users"
    users: List[UserItem]


class ChannelListResponse(BaseModel):
    request: Literal["get_channels"] = "get_channels"
    channels: List[ChannelItem]


class MessageListResponse(BaseModel):
    request: Literal["load_messages"] = "load_messages"
    messages: List[MessageItem]
