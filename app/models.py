from datetime import datetime
from pydantic import field_validator
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password: str
    status: int = Field(default=0)


class UserPublic(UserBase):
    id: int


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class ArticleBase(SQLModel):
    title: str = Field(index=True, min_length=1, max_length=50)


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(ArticleBase):
    state: str = Field(default="", max_length=50)
    state_content: str | None = Field(default="")
    content: str | None = Field(default=None)
    content_summary: str | None = Field(default=None)
    url_to_info: str | None = Field(default=None)


class Article(ArticleBase, table=True):
    __tablename__ = "article_info"

    id: int | None = Field(default=None, primary_key=True)
    content: str | None = Field(default=None)
    content_summary: str | None = Field(default="")
    url_to_info: str | None = Field(default=None)
    status: int = Field(default="0")
    state: str = Field(default="", max_length=50)
    state_content: str | None = Field(default="")
    owner_id: int = Field(nullable=False)
    cdate: datetime = Field(sa_column=Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP"), default=None)


class ArticleCreatePublic(ArticleBase):
    id: int


class ArticlePublic(ArticleBase):
    id: int
    content_summary: str
    cdate: str

    @field_validator('cdate', mode="before")
    def format_cdate(cls, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value


class ArticlesPublic(SQLModel):
    data: list[ArticlePublic]
    count: int


class ArticleInfoPublic(ArticleBase):
    content: str | None
    state: str
    url_to_info: dict | None


class ArticleStatePublic(SQLModel):
    state: str
    info_message: str | None


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
