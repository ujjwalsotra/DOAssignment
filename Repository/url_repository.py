from sqlalchemy.orm import Session
from Entity.urlentity import URLDB
from typing import Optional

class UrlRepository:

    def save(self, url: URLDB, db: Session) -> URLDB:
        db.add(url)
        db.commit()
        db.refresh(url)
        return url

    def find_by_short_code(self, short_code: str, db: Session) -> Optional[URLDB]:
        return db.query(URLDB).filter(
            URLDB.short_code == short_code
        ).first()

    def find_by_long_url(self, long_url: str, db: Session) -> Optional[URLDB]:
        return db.query(URLDB).filter(
            URLDB.long_url == long_url
        ).first()

    def increment_access(self, short_code: str, db: Session):
        from sqlalchemy import update
        db.execute(
            update(URLDB)
            .where(URLDB.short_code == short_code)
            .values(access_count=URLDB.access_count + 1)
        )
        db.commit()

    def exists(self, short_code: str, db: Session) -> bool:
        return self.find_by_short_code(short_code, db) is not None