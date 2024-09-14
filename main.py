import os

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core import log
from app.core.config import settings

if settings.HTTP_PROXY:
    os.environ['http_proxy'] = settings.HTTP_PROXY
    os.environ['https_proxy'] = settings.HTTP_PROXY

logger = log.setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return "welcome to storm server"


if __name__ == "__main__":
    if settings.ENVIRONMENT == "local":
        reload = True
    else:
        reload = False
    uvicorn.run(app='main:app', host="0.0.0.0", port=8080, reload=reload)
