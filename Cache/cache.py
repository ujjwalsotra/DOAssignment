from datetime import datetime, timedelta, timezone
from typing import Optional

class InmemoryCache:
    def __init__(self,ttl_seconds:int = 300):
        self._store={}
        self._ttl = ttl_seconds

    def get(self,key:str)->Optional[str]:
        entry = self._store.get(key)
        if not entry:
            return None
        if datetime.now(timezone.utc)>entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]
    
    def set(self,key:str,value:str):
        self._store[key]={
            "value":value,
            "expires_at":datetime.now(timezone.utc)+timedelta(seconds=self._ttl)
        }
    
    def delete(self,key:str):
        self._store.pop(key,None)


cache = InmemoryCache()