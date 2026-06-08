from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import logging

from database import get_db, engine, Base
from Entity.urlentity import ShortenRequest, UrlResponse
from Repository.url_repository import UrlRepository
from Service.url_service import UrlService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")
repo = UrlRepository()
service = UrlService(repo)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/health")
def get_health():
    return {"status": "200-Healthy"}

@app.post("/shorten", status_code=201, response_model=UrlResponse)
def shorten(request: ShortenRequest, db: Session = Depends(get_db)):
    logger.info(f"Shortening URL {request.long_url}")
    return service.shorten(request, db)

@app.get("/meta/{short_code}", response_model=UrlResponse)  # ← BEFORE /{short_code}
def get_metadata(short_code: str, db: Session = Depends(get_db)):
    return service.get_metadata(short_code, db)

@app.get("/{short_code}")  # ← AFTER /meta/
def redirect(short_code: str, db: Session = Depends(get_db)):
    long_url = service.resolve(short_code, db)
    return RedirectResponse(url=long_url)