import json
import logging
import os
from shutil import rmtree
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from sqlmodel import func, select

from app.core.config import settings
from app.crud import create_article, update_article
from app.api.deps import CurrentUser, SessionDep
from app.core import storm
from app.models import Article, ArticleCreate, ArticleUpdate, ArticleCreatePublic, ArticleStatePublic, ArticleInfoPublic, ArticlesPublic, Message

router = APIRouter()


@router.post("/start-model", response_model=ArticleCreatePublic)
def start_model(*, session: SessionDep, current_user: CurrentUser, article_in: ArticleCreate) -> Any:
    if session.query(Article).filter(Article.title == article_in.title, Article.owner_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Article with this title already exists")
    if not storm.check_sensitive_info(article_in.title):
        raise HTTPException(status_code=400, detail="Sorry, the topic you entered contains sensitive information. Please try another topic that interests you.")

    return create_article(session=session, article_in=article_in, owner_id=current_user.id)


@router.post("/{article_id}/update-sse")
def update_sse(*, session: SessionDep, current_user: CurrentUser, article_id: int):
    json_contents = run_model(article_id, session, current_user)
    return StreamingResponse(json_contents, media_type='text/event-stream')


def run_model(article_id: int, session: SessionDep, current_user: CurrentUser):
    try:
        article = session.get(Article, article_id)
        if not article:
            raise Exception("Article not found")
        if not article.status == 1:
            raise Exception("Article is not available")
        if not article.owner_id == current_user.id:
            raise Exception("Not enough permissions")

        runner = None
        if article.state == "initiated":
            runner = storm.set_storm_runner(current_user.username)
            update_article(session=session, db_article=article, article_in=ArticleUpdate(title=article.title, state="pre_writing"))
            yield json.dumps({"event_id": 1, "message": "Have successfully set up llm provider", "is_done": False, "code": 200}) + '\n\n'

        if article.state == "pre_writing":
            yield json.dumps({"event_id": 2, "message": "I am brain**STORM**ing now to research the topic. (This may take 2-3 minutes.)", "is_done": False, "code": 200}) + '\n\n'

            if runner is None:
                runner = storm.set_storm_runner(current_user.username)

            runner.run(
                topic=article.title,
                do_research=True,
                do_generate_outline=True,
                do_generate_article=False,
                do_polish_article=False)
            print("Have successfully finished the running research and generate_outline process")

            update_article(session=session, db_article=article, article_in=ArticleUpdate(title=article.title, state="final_writing"))
            yield json.dumps({"event_id": 3, "message": "brain ** STORM ** ing complete!", "is_done": False, "code": 200}) + '\n\n'

        if article.state == "final_writing":
            yield json.dumps({"event_id": 4, "message": "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)", "is_done": False, "code": 200}) + '\n\n'

            if runner is None:
                runner = storm.set_storm_runner(current_user.username)

            runner.run(
                topic=article.title,
                do_research=False,
                do_generate_outline=False,
                do_generate_article=True,
                do_polish_article=True,
                remove_duplicate=False)
            print("Have successfully finished the running generate_article and polish_article process")
            runner.post_run()
            print("Have successfully finished the article generation process")
            runner.summary()
            print("Finished running runner!")

            update_article(session=session, db_article=article, article_in=ArticleUpdate(title=article.title, state="update_database"))
            yield json.dumps({"event_id": 5, "message": "information synthesis complete!", "is_done": False, "code": 200}) + '\n\n'

        if article.state == "update_database":
            if runner is None:
                directory = os.path.join(settings.OUTPUT_DIR, current_user.username, article.title.replace(' ', '_').replace('/', '_'))
            else:
                directory = runner.article_output_dir
            print(f"Article_output_dir: {directory}")

            try:
                with open(f"{directory}/storm_gen_article_polished.txt") as f:
                    final_content = f.read()
                with open(f"{directory}/url_to_info.json") as f:
                    final_url_to_info = f.read()

                # TODO can add other files ...

                yield json.dumps({"event_id": 6, "message": "Updating article in database", "code": 200, "is_done": False}) + '\n\n'

                try:
                    update_article(session=session, db_article=article, article_in=ArticleUpdate(
                        title=article.title,
                        content=final_content,
                        url_to_info=final_url_to_info,
                        state="completed"))

                    if settings.DELETE_ARTICLE_OUTPUT_DIR:
                        rmtree(directory)

                    yield json.dumps({"event_id": 7, "message": "Have successfully uploaded to db, sending article content back!", "is_done": True, "code": 200}) + '\n\n'
                except Exception as e:
                    yield json.dumps({"event_id": 7, "message": f"Failed to upload article to database: {str(e)}", "code": 500, "is_done": False}) + '\n\n'
            except Exception as e:
                yield json.dumps({"event_id": 6, "message": f"Failed parsing file, error is: {e}", "code": 500, "is_done": False}) + '\n\n'
        print("Fully parsed file, sending response back!\n")
    except Exception as e:
        print("Error in create_article: ", e)
        yield json.dumps({"event_id": 1, "message": f"Failed to create article, error is: {e}", "is_done": True, "code": 500}) + '\n\n'


@router.get("/{article_id}/state", response_model=ArticleStatePublic)
def get_state(*, session: SessionDep, current_user: CurrentUser, article_id: int) -> Any:
    item = session.get(Article, article_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    data_dict = {
        "initiated": "Start set up llm provider. (Step 1 / 4)",
        "pre_writing": "Start research and generate_outline. (Step 2 / 4)",
        "final_writing": "Start generate_article and polish_article. (Step 3 / 4)",
        "update_database": "Start update database (Step 4 / 4)",
        "completed": "",
    }
    return ArticleStatePublic(info_message=data_dict.get(item.state), state=item.state)


@router.get("/{article_id}", response_model=ArticleInfoPublic)
def get_info(*, session: SessionDep, current_user: CurrentUser, article_id: int) -> Any:
    item = session.get(Article, article_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.get("/", response_model=ArticlesPublic)
def read_articles(*, session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    count_statement = (
        select(func.count())
        .select_from(Article)
        .where(Article.owner_id == current_user.id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Article)
        .where(Article.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()

    return ArticlesPublic(data=items, count=count)


@router.delete("/{article_id}")
def delete_item(*, session: SessionDep, current_user: CurrentUser, article_id: int) -> Message:
    item = session.get(Article, article_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
