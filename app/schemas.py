from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    description: str | None = None


class PostCreate(PostBase):
    pass


class DeletePost(BaseModel):
    id :int

class ReturnPost(BaseModel):
    id :int

class Post(PostBase):
    id: int
    owner_id: str

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreateAndGet(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: list[Post] = []

    class Config:
        orm_mode = True
