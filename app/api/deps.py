from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated, Type

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from redis import Redis
from sqlmodel import Session

from app.core import log
from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.core.redis import redis_client
from app.models import TokenPayload, User

logger = log.setup_logging()

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


@contextmanager
def redis_context():
    conn = redis_client
    try:
        yield conn
    finally:
        conn.close()


def get_redis():
    with redis_context() as redis:
        yield redis


SessionDep = Annotated[Session, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> Type[User]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as e:
        logger.error(f"Invalid token:{token}, error:{e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.status == 1:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
