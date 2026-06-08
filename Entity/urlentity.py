from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer
from database import Base

class URLDB(Base):
    __tablename__ = "urls"

    short_code   = Column(String, primary_key=True, index=True)
    long_url     = Column(String, nullable=False)
    access_count = Column(Integer, default=0)
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ShortenRequest(BaseModel):
    long_url: str
    custom_alias: Optional[str] = Field(default=None,
                                        min_length=3,
                                        max_length=20,
                                        pattern="^[a-zA-Z0-9-_]+$"
                                    )

class UrlResponse(BaseModel):
    short_code:   str
    long_url:     str
    short_url:    str
    created_at:   datetime
    access_count: int
