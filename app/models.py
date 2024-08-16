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
    title: str = Field(min_length=1, max_length=255)


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(ArticleBase):
    state: str = Field(default="", max_length=50)
    content: str | None = Field(default=None)
    url_to_info: str | None = Field(default=None)


class Article(ArticleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str | None = Field(default=None)
    url_to_info: str | None = Field(default=None)
    status: int = Field(default="0")
    state: str = Field(default="", max_length=50)
    owner_id: int = Field(nullable=False)


class ArticleCreatePublic(ArticleBase):
    id: int


class ArticlesPublic(SQLModel):
    data: list[ArticleCreatePublic]
    count: int


class ArticleInfoPublic(ArticleBase):
    content: str | None
    url_to_info: str | None
    state: str


class ArticleStatePublic(SQLModel):
    state: str
    info_message: str


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
