from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core.security import get_password_hash, verify_password
from app.models import Message, User, UserCreate, UpdatePassword, UserPublic, UsersPublic

router = APIRouter()


@router.get("/", response_model=UsersPublic)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(user_id: int, session: SessionDep) -> Any:
    user = session.get(User, user_id)
    return user


@router.post("/", response_model=UserPublic)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    user = crud.get_user_by_username(session=session, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="The user with this username already exists in the system.")

    user = crud.create_user(session=session, user_create=user_in)

    return user


@router.patch("/password", response_model=Message)
def update_password(*, session: SessionDep, body: UpdatePassword, current_user: CurrentUser) -> Any:
    if not verify_password(body.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current one")
    current_user.password = get_password_hash(body.new_password)

    session.add(current_user)
    session.commit()

    return Message(message="Password updated successfully")
