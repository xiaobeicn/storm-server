import json
import os
import time
from shutil import rmtree
from typing import Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import func, select, desc
from starlette import status

from app import util
from app.api.deps import CurrentUser, SessionDep, RedisDep
from app.constants import ArticleStatus, ReviewStatus, ArticleState
from app.core import storm, log
from app.core.config import settings
from app.crud import create_article, update_article, delete_article, reset_article
from app.models import Article, ArticleCreate, ArticleUpdate, ArticleCreatePublic, ArticleStatePublic, ArticleInfoPublic, ArticlesPublic, Message

logger = log.setup_logging()

router = APIRouter()


@router.post("/start-model", response_model=ArticleCreatePublic)
def start_model(*, session: SessionDep, redis_client: RedisDep, current_user: CurrentUser, article_in: ArticleCreate, background_tasks: BackgroundTasks) -> Any:
    user_id = current_user.id

    item = session.query(Article).filter_by(title=article_in.title, owner_id=user_id).first()

    if item and item.status == ArticleStatus.VALID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="对不起，主题已经存在，请勿重复创建")

    response = storm.check_sensitive_info(article_in.title)
    if not response:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="系统异常")

    check_result = response['choices'][0]['message']['content']

    if check_result in [ReviewStatus.POINTLESS, ReviewStatus.SENSITIVE]:
        if check_result == ReviewStatus.POINTLESS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="对不起，请输入有具体意义的主题")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="对不起，您输入的主题包含敏感信息，请尝试其他您感兴趣的主题")

    if item and item.status == ArticleStatus.DELETED:
        article = reset_article(session=session, db_article=item)
    else:
        article = create_article(session=session, article_in=article_in, owner_id=user_id)

    background_tasks.add_task(_article_generate, session, redis_client=redis_client, user_id=user_id, article=article)

    return article


def _article_generate(session: SessionDep, redis_client: RedisDep, user_id: int, article: Article):
    redis_key = _redis_key(article.id)
    tmp_state = article.state

    if not article.state == ArticleState.INIT:
        redis_client.rpush(redis_key, json.dumps({"state": tmp_state, "message": "Not initiated", "is_done": False, "code": 500}))
        return

    logger.info(f"Started running runner! State:{tmp_state}")

    tmp_state = "pre_writing"
    redis_client.rpush(redis_key, json.dumps({"state": tmp_state, "message": "Preparing writing", "is_done": False, "code": 200}))

    runner = storm.set_storm_runner(user_id)

    logger.info(f"Started set storm runner! State:{tmp_state}")

    if tmp_state == "pre_writing":
        callback_handler = storm.CallbackHandler(redis_client, redis_key)
        runner.run(
            topic=article.title,
            do_research=True,
            do_generate_outline=True,
            do_generate_article=False,
            do_polish_article=False,
            callback_handler=callback_handler
        )
        tmp_state = "pre_writing_end"
        redis_client.rpush(redis_key, json.dumps({"state": tmp_state, "message": "Start writing and drafting your article (Step 4 / 4)", "is_done": False, "code": 200}))

    if tmp_state == "pre_writing_end":
        runner.run(
            topic=article.title,
            do_research=False,
            do_generate_outline=False,
            do_generate_article=True,
            do_polish_article=True,
            remove_duplicate=False
        )
        runner.post_run()
        tmp_state = "generate_article_end"
        redis_client.rpush(redis_key, json.dumps({"state": tmp_state, "message": "generate article and polish article end", "is_done": False, "code": 200}))

    runner.summary()
    logger.info(f"Finished running runner! State:{tmp_state}")

    if tmp_state == "generate_article_end":
        directory = util.article_directory(user_id, article.title)
        logger.info(f"Article_output_dir: {directory}")

        try:
            with open(f"{directory}/storm_gen_article_polished.txt") as f:
                final_content = f.read()
            with open(f"{directory}/url_to_info.json") as f:
                final_url_to_info = f.read()

            try:
                summary = final_content
                if summary[0] == '#':
                    summary = ''.join(summary.split('\n')[1:])

                update_article(session=session, db_article=article, article_in=ArticleUpdate(
                    title=article.title,
                    content_summary=summary[:200],
                    content=final_content,
                    url_to_info=final_url_to_info,
                    state="finish",
                    state_content=""))

                if settings.DELETE_ARTICLE_OUTPUT_DIR:
                    rmtree(directory)

                logger.info("Finished updating article in db")
                redis_client.rpush(redis_key, json.dumps({"state": ArticleState.DONE, "message": "", "is_done": True, "code": 200}))
            except Exception as e:
                logger.error(f"Failed to update article in db: {e}")
                redis_client.rpush(redis_key, json.dumps({"state": "fail_db", "message": "Failed to update article in db", "is_done": False, "code": 500}))
        except Exception as e:
            logger.error(f"Failed to parse file: {e}")
            redis_client.rpush(redis_key, json.dumps({"state": "fail_file", "message": "Failed to parse file", "is_done": False, "code": 500}))

    redis_client.rpush(redis_key, "END")

    logger.info("Finished article generation")


def _listen_to_stream(session: SessionDep, redis_client: RedisDep, user_id: int, article_id: int):
    try:
        article = session.get(Article, article_id)
        if not article:
            raise Exception("Article not found")
        if not article.status == ArticleStatus.VALID:
            raise Exception("Article is not available")
        if not article.owner_id == user_id:
            raise Exception("Not enough permissions")

        if article.state == ArticleState.DONE:
            yield "data: " + json.dumps({"state": ArticleState.DONE, "message": "", "is_done": True, "code": 200})
            return

        redis_key = _redis_key(article_id)

        if not redis_client.exists(redis_key):
            return Exception("Article is not available")

        error_flag = 0
        while True:
            data = redis_client.lpop(redis_key)

            if data:
                error_flag = 0
                if data == b"END":  # 检查是否是结束标志
                    break
                try:
                    json_obj = json.loads(data.decode('utf-8'))

                    if json_obj["state"] != "":
                        tmp_state = json_obj["state"]
                        is_done = json_obj["is_done"]
                        code = json_obj["code"]
                        update_article(session=session, db_article=article, article_in=ArticleUpdate(title=article.title, state=tmp_state, state_content=json_obj["message"]))

                        yield "data: " + json.dumps({"state": tmp_state, "is_done": is_done, "code": code}) + '\n\n'
                except ValueError as e:
                    logger.error(f"Failed to parse json: {e}")
            else:
                if error_flag > 300:  # 5分钟没变化跳出
                    break
                time.sleep(1)
                error_flag += 1
    except Exception as e:
        logger.error(f'Error in listen_to_stream: {e}')
        yield "data: " + json.dumps({"state": "fail_listen_to_stream", "is_done": False, "code": 500}) + '\n\n'


def _redis_key(article_id: int):
    return f"storm:article:generation:{article_id}"


@router.get("/{article_id}/update-sse")
def update_sse(*, session: SessionDep, redis_client: RedisDep, current_user: CurrentUser, article_id: int):
    return StreamingResponse(_listen_to_stream(session, redis_client, current_user.id, article_id), media_type="text/event-stream")


@router.get("/{article_id}/state", response_model=ArticleStatePublic)
def get_state(*, session: SessionDep, current_user: CurrentUser, article_id: int) -> Any:
    item = session.get(Article, article_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="主题不存在")
    if not item.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    return ArticleStatePublic(info_message=item.state_content, state=item.state)


@router.get("/{article_id}", response_model=ArticleInfoPublic)
def get_info(*, session: SessionDep, current_user: CurrentUser, article_id: int) -> Any:
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="主题不存在")
    if not article.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    if article.content:
        if article.content[0] == '#':
            article.content = '\n'.join(article.content.split('\n')[1:])
        article.url_to_info = util.construct_citation_dict(article.url_to_info)
        article.content = util.add_inline_citation_link(article.content, article.url_to_info)

    return article


@router.get("/", response_model=ArticlesPublic)
def read_articles(*, session: SessionDep, current_user: CurrentUser, page: int = Query(1, gt=0, le=100), pagesize: int = Query(10, gt=0, le=100), keyword: str | None = None) -> Any:
    skip = (page - 1) * pagesize
    count_statement = (
        select(func.count())
        .select_from(Article)
        .where(Article.owner_id == current_user.id, Article.status == ArticleStatus.VALID)
    )
    statement = (
        select(Article.id, Article.title, Article.content_summary, Article.cdate)
        .select_from(Article)
        .where(Article.owner_id == current_user.id, Article.status == ArticleStatus.VALID)
        .offset(skip)
        .limit(pagesize)
        .order_by(desc(Article.cdate))
    )
    if keyword:
        count_statement = count_statement.where(Article.title.contains(keyword))
        statement = statement.where(Article.title.contains(keyword))
    count = session.exec(count_statement).one()
    items = session.exec(statement).all()

    return ArticlesPublic(data=items, count=count)


@router.delete("/{article_id}")
def delete_item(*, session: SessionDep, current_user: CurrentUser, article_id: int) -> Message:
    article = session.get(Article, article_id)
    logger.info(f"delete article {article_id}")
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="主题不存在")
    if not article.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    delete_article(session=session, db_article=article)
    if not article.status == ArticleStatus.DELETED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="主题删除失败")
    if not settings.DELETE_ARTICLE_OUTPUT_DIR:
        directory = util.article_directory(current_user.id, article.title)
        if os.path.exists(directory):
            rmtree(directory)
    return Message(message="主题删除成功")
