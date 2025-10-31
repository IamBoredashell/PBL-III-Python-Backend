import pydantic
import enum
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
    completed="completed"

class UserRole(str, enum.Enum):
    sys_admin="sys_admin"
    teacher="teacher"
    student="student"

class AddUserRequest(pydantic.BaseModel):
    email: pydantic.EmailStr
    username: pydantic.constr(min_length=4,max_length=64)
    password: pydantic.constr(min_length=8,max_length=64)
    role:  UserRole 
    first_name:  pydantic.constr(min_length=1,max_length=64)
    last_name:  pydantic.constr(min_length=1,max_length=64)

#User route

class UserInfoResponse(pydantic.BaseModel):
    email: pydantic.EmailStr
    username: pydantic.constr(min_length=4,max_length=64)
    role:  UserRole 
    first_name:  pydantic.constr(min_length=1,max_length=64)
    last_name:  pydantic.constr(min_length=1,max_length=64)
