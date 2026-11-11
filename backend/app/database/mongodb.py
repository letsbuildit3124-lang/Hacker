import asyncio
import time
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings
from backend.app.utils.logger import logger

class InMemoryCollection:
    """Async in-memory MongoDB-compatible collection for local testing / offline fallback."""
    def __init__(self, name: str):
        self.name = name
        self._docs: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def insert_one(self, doc: Dict[str, Any]):
        async with self._lock:
            self._docs.append(dict(doc))
        return type("InsertResult", (), {"acknowledged": True})()

    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            for d in self._docs:
                if all(d.get(k) == v for k, v in filter_dict.items()):
                    return dict(d)
        return None

    def find(self, filter_dict: Optional[Dict[str, Any]] = None):
        filter_dict = filter_dict or {}
        class Cursor:
            def __init__(self, docs, f_dict):
                self._docs = [
                    dict(d) for d in docs
                    if all(d.get(k) == v for k, v in f_dict.items())
                ]
            def sort(self, key_or_list, direction=None):
                if isinstance(key_or_list, list):
                    key, direction = key_or_list[0]
                else:
                    key = key_or_list
                    direction = direction or 1
                reverse = direction < 0
                self._docs.sort(key=lambda x: str(x.get(key, "")), reverse=reverse)
                return self
            async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
                if length is None:
                    return list(self._docs)
                return list(self._docs[:length])
        return Cursor(self._docs, filter_dict)

    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], upsert: bool = False):
        async with self._lock:
            set_ops = update_dict.get("$set", {})
            for d in self._docs:
                if all(d.get(k) == v for k, v in filter_dict.items()):
                    for k, v in set_ops.items():
                        d[k] = v
                    return type("UpdateResult", (), {"matched_count": 1, "modified_count": 1})()
            if upsert:
                new_doc = dict(filter_dict)
                new_doc.update(set_ops)
                self._docs.append(new_doc)
                return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0, "upserted_id": True})()
        return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0})()

    async def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        filter_dict = filter_dict or {}
        async with self._lock:
            return sum(1 for d in self._docs if all(d.get(k) == v for k, v in filter_dict.items()))


class ResilientCollectionProxy:
    """
    Transparent proxy that delegates to the active MongoDB collection,
    and automatically falls back to an in-memory collection upon network or SSL errors.
    """
    def __init__(self, name: str, mongo_instance: 'MongoDB'):
        self.name = name
        self._mongo = mongo_instance

    def _get_real(self):
        if self._mongo.is_connected and self._mongo.db is not None:
            return self._mongo.db[self.name]
        return None

    def _get_fallback(self) -> InMemoryCollection:
        if self.name not in self._mongo._fallback_db:
            self._mongo._fallback_db[self.name] = InMemoryCollection(self.name)
        return self._mongo._fallback_db[self.name]

    def _handle_error(self, err: Exception):
        logger.warning(f"[MongoDB Proxy] Shard/Network exception on '{self.name}' ({err}). Falling back to in-memory store.")
        self._mongo.is_connected = False

    async def insert_one(self, doc: Dict[str, Any], *args, **kwargs):
        real = self._get_real()
        if real is not None:
            try:
                return await real.insert_one(doc, *args, **kwargs)
            except Exception as e:
                self._handle_error(e)
        return await self._get_fallback().insert_one(doc)

    async def find_one(self, filter_dict: Dict[str, Any], *args, **kwargs) -> Optional[Dict[str, Any]]:
        real = self._get_real()
        if real is not None:
            try:
                return await real.find_one(filter_dict, *args, **kwargs)
            except Exception as e:
                self._handle_error(e)
        return await self._get_fallback().find_one(filter_dict)

    def find(self, filter_dict: Optional[Dict[str, Any]] = None, *args, **kwargs):
        filter_dict = filter_dict or {}
        proxy = self

        class ResilientCursor:
            def __init__(self):
                real = proxy._get_real()
                self._real_cursor = real.find(filter_dict, *args, **kwargs) if real is not None else None
                self._fallback_cursor = proxy._get_fallback().find(filter_dict)

            def sort(self, *s_args, **s_kwargs):
                if self._real_cursor is not None:
                    try:
                        self._real_cursor.sort(*s_args, **s_kwargs)
                    except Exception:
                        pass
                self._fallback_cursor.sort(*s_args, **s_kwargs)
                return self

            async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
                if self._real_cursor is not None:
                    try:
                        return await self._real_cursor.to_list(length)
                    except Exception as e:
                        proxy._handle_error(e)
                return await self._fallback_cursor.to_list(length)

        return ResilientCursor()

    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], *args, **kwargs):
        real = self._get_real()
        if real is not None:
            try:
                return await real.update_one(filter_dict, update_dict, *args, **kwargs)
            except Exception as e:
                self._handle_error(e)
        upsert = kwargs.get("upsert", False)
        return await self._get_fallback().update_one(filter_dict, update_dict, upsert=upsert)

    async def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None, *args, **kwargs) -> int:
        filter_dict = filter_dict or {}
        real = self._get_real()
        if real is not None:
            try:
                return await real.count_documents(filter_dict, *args, **kwargs)
            except Exception as e:
                self._handle_error(e)
        return await self._get_fallback().count_documents(filter_dict)


class MongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_connected = False
        self._fallback_db: Dict[str, InMemoryCollection] = {
            "sessions": InMemoryCollection("sessions"),
            "messages": InMemoryCollection("messages"),
            "evaluations": InMemoryCollection("evaluations"),
            "batches": InMemoryCollection("batches")
        }

    async def connect(self):
        try:
            # Configure TLS with certifi if available for cloud Atlas clusters
            kwargs = {
                "serverSelectionTimeoutMS": 4000,
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 5000
            }
            try:
                import certifi
                kwargs["tlsCAFile"] = certifi.where()
            except ImportError:
                pass

            client = AsyncIOMotorClient(settings.MONGODB_URI, **kwargs)
            await client.admin.command('ping')
            self.client = client
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            logger.info(f"Connected to MongoDB at {settings.MONGODB_URI}, database: {settings.DATABASE_NAME}")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB ({e}). Operating with in-memory resilient fallback store.")
            self.is_connected = False

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    def get_collection(self, name: str) -> ResilientCollectionProxy:
        return ResilientCollectionProxy(name, self)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        coll = self.get_collection("sessions")
        doc = await coll.find_one({"sessionId": session_id})
        return doc

    async def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        coll = self.get_collection("messages")
        cursor = coll.find({"sessionId": session_id}).sort("timestamp", 1)
        return await cursor.to_list(1000)

    async def save_message(
        self,
        session_id: str,
        sender: str,
        text: str,
        timestamp: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        coll = self.get_collection("messages")
        msg = {
            "sessionId": session_id,
            "sender": sender,
            "text": text,
            "timestamp": timestamp or int(time.time() * 1000),
            "metadata": metadata or {}
        }
        await coll.insert_one(msg)
        return msg

    async def get_evaluation(self, session_id: str) -> Optional[Dict[str, Any]]:
        coll = self.get_collection("evaluations")
        doc = await coll.find_one({"sessionId": session_id})
        return doc

    async def save_evaluation(self, session_id: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        coll = self.get_collection("evaluations")
        evaluation_data["sessionId"] = session_id
        res = await coll.update_one({"sessionId": session_id}, {"$set": evaluation_data}, upsert=True)
        return evaluation_data

db = MongoDB()
