import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (CurrentUser, SessionDep, )
from app.core.config import settings
from app.models import (
    Message,
    User,
    UserCreate,
    UserPublic,
    UsersPublic,
)

router = APIRouter()


@router.get("/", response_model=UsersPublic)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post("/", response_model=UserPublic)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    user = crud.get_user_by_username(session=session, username=user_in.username)
    if user:
        raise HTTPException(status_code=400,detail="The user with this email already exists in the system." )

    user = crud.create_user(session=session, user_create=user_in)

    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(user_id: int, session: SessionDep) -> Any:
    user = session.get(User, user_id)
    return user
