import hashlib
import string
import random
from sqlalchemy.orm import Session
from Entity.urlentity import URLDB, ShortenRequest, UrlResponse
from Repository.url_repository import UrlRepository
from Cache.cache import cache
from fastapi import HTTPException
import logging
import os

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/")  # your DO domain
CODE_LENGTH = 7

class UrlService:
    def __init__(self, repo: UrlRepository):
        self.repo = repo

    def _generate_short_code(self) -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=CODE_LENGTH))

    def shorten(self, request: ShortenRequest, db: Session) -> UrlResponse:
        # use custom alias if provided
        short_code = request.custom_alias or self._generate_short_code()

        # handle collision
        max_attempts = 5
        attempts = 0
        while self.repo.exists(short_code, db):
            if request.custom_alias:
                # custom alias taken — fail fast
                raise HTTPException(
                    status_code=409,
                    detail=f"Alias '{short_code}' already taken"
                )
            short_code = self._generate_short_code()
            attempts += 1
            if attempts >= max_attempts:
                raise HTTPException(
                    status_code=500,
                    detail="Could not generate unique code"
                )

        # save to DB
        db_url = URLDB(
            short_code=short_code,
            long_url=request.long_url
        )
        saved = self.repo.save(db_url, db)
        
        # cache it
        cache.set(short_code, request.long_url)
        logger.info(f"Shortened {request.long_url} → {short_code}")

        return self._to_response(saved)

    def resolve(self, short_code: str, db: Session) -> str:
        # check cache first
        cached = cache.get(short_code)
        if cached:
            logger.info(f"Cache hit for {short_code}")
            self.repo.increment_access(short_code, db)
            return cached

        # cache miss — go to DB
        logger.info(f"Cache miss for {short_code}")
        url = self.repo.find_by_short_code(short_code, db)
        if not url:
            raise HTTPException(status_code=404, detail="URL not found")

        # populate cache
        cache.set(short_code, url.long_url)
        self.repo.increment_access(short_code, db)
        return url.long_url

    def get_metadata(self, short_code: str, db: Session) -> UrlResponse:
        url = self.repo.find_by_short_code(short_code, db)
        if not url:
            raise HTTPException(status_code=404, detail="URL not found")
        return self._to_response(url)

    def _to_response(self, url: URLDB) -> UrlResponse:
        return UrlResponse(
            short_code=url.short_code,
            long_url=url.long_url,
            short_url=f"{BASE_URL}{url.short_code}",
            created_at=url.created_at,
            access_count=url.access_count
        )