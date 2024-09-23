from typing import Any

from sqlmodel import Session, select

from app.enum import EnumArticleStatus, EnumArticleState
from app.core.security import verify_password, get_password_hash
from app.models import Article, ArticleCreate, ArticleUpdate, User, UserCreate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"password": get_password_hash(user_create.password), "status": 1}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_user_by_username(*, session: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, username: str, password: str) -> User | None:
    db_user = get_user_by_username(session=session, username=username)
    if not db_user:
        return None
    if not verify_password(password, db_user.password):
        return None
    return db_user


def create_article(*, session: Session, article_in: ArticleCreate, owner_id: int) -> Article:
    db_article = Article.model_validate(article_in, update={"owner_id": owner_id, "status": EnumArticleStatus.VALID, "state": EnumArticleState.INIT})
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article


def update_article(*, session: Session, db_article: Article, article_in: ArticleUpdate) -> Any:
    update_dict = article_in.model_dump(exclude_unset=True)
    db_article.sqlmodel_update(update_dict)
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article


def delete_article(*, session: Session, db_article: Article) -> Any:
    db_article.sqlmodel_update({"status": EnumArticleStatus.DELETED})
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article


def reset_article(*, session: Session, db_article: Article) -> Any:
    db_article.sqlmodel_update({"status": EnumArticleStatus.VALID, "state": EnumArticleState.INIT, "content_summary": "", "content": None, "url_to_info": None})
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article
