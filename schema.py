import pydantic
import enum
import typing
#Token 
class TokenPayload(pydantic.BaseModel):
    sub: str
    username: str
    exp: int 


#Login route
class LoginRequest(pydantic.BaseModel):
    email: pydantic.EmailStr
    password: pydantic.constr(min_length=8,max_length=64) 

class LoginResponse(pydantic.BaseModel):
    token: str
#admin route
class UserStatus(str, enum.Enum):
    active="active"
    banned="banned"
    deleted="deleted"

class EditUserRequest(pydantic.BaseModel):
    user_id: int
    email: str
    username: str
    user_role: str
    status: UserStatus
    first_name: typing.Optional[str]=None
    last_name:  typing.Optional[str]=None

class UserRole(str, enum.Enum):
    sys_admin="sys_admin"
    teacher="teacher"
    student="student"

class ChannelStatus(str, enum.Enum):
    active="active"
    banned="banned"
    deleted="deleted"

class UserChannelStatus(str, enum.Enum):
    active="active"
    banned="banned"
    deleted="deleted"

class AddUserRequest(pydantic.BaseModel):
    email: pydantic.EmailStr
    username: pydantic.constr(min_length=4,max_length=64)
    password: pydantic.constr(min_length=8,max_length=64)
    role: UserRole 
    first_name:  pydantic.constr(min_length=1,max_length=64)
    last_name:  pydantic.constr(min_length=1,max_length=64)

class AddChannelRequest(pydantic.BaseModel):
    name: str
    status: ChannelStatus 

class DeleteChannelRequest(pydantic.BaseModel):
    channel_id: int
    name: str

class EditUserChannelRequest(pydantic.BaseModel):
    channel_id: int
    user_id: int 
    status: UserChannelStatus
    permission: int 

class userList(pydantic.BaseModel):
    id: int
    username: str
    email: pydantic.EmailStr
    status: str
    user_role:UserRole
    first_name: str
    last_name: str

class getUserListResponse(pydantic.BaseModel):
    users: typing.List[userList]
    

class channelList(pydantic.BaseModel):
    id : int 
    name : str
    status : str

class getChannelListResponse(pydantic.BaseModel):
    channel: typing.List[channelList]

class ChannelUserInfo(pydantic.BaseModel):
    channel_id: int
    channel_name: str
    user_id: int
    username: str
    status: str
    permission: int

class getUserInfoAtChannel(pydantic.BaseModel):
    UserInfo: typing.List[ChannelUserInfo]
#User route

class UserInfoResponse(pydantic.BaseModel):
    email: pydantic.EmailStr
    username: pydantic.constr(min_length=4,max_length=64)
    role:  UserRole 
    first_name:  pydantic.constr(min_length=1,max_length=64)
    last_name:  pydantic.constr(min_length=1,max_length=64)

#Chats route

# ===== Requests =====
class BaseRequest(pydantic.BaseModel):
    request : str

class GetUsersRequest(BaseRequest):
    request : typing.Literal["get_users"]

class GetChannelsRequest(BaseRequest):
    request : typing.Literal["get_channels"]

class LoadMessagesRequest(BaseRequest):
    request : typing.Literal["load_messages"]
    channel_id: int
    limit: typing.Optional[int] = 50

# ===== Responses =====
class UserItem(pydantic.BaseModel):
    id: int
    username: str

class ChannelItem(pydantic.BaseModel):
    id: int
    name: str
    last_message: typing.Optional[str]

class MessageItem(pydantic.BaseModel):
    sender_id: int
    content: str
    created_at: str

class UserListResponse(pydantic.BaseModel):
    type: typing.Literal["user_list"]
    data: typing.List[UserItem]

class ChannelListResponse(pydantic.BaseModel):
    type: typing.Literal["channel_list"]
    data: typing.List[ChannelItem]

class MessageListResponse(pydantic.BaseModel):
    type: typing.Literal["messages"]
    data: typing.List[MessageItem]

