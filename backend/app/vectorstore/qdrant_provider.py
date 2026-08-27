
# ===== app/vectorstore/qdrant_provider.py =====
import asyncio
from qdrant_client import AsyncQdrantClient, models
from app.vectorstore.base import VectorStoreProvider
from app.core.config import settings
from app.core.logging_config import logger

class QdrantProvider(VectorStoreProvider):
    def __init__(self):
        try:
            self.client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=getattr(settings, "QDRANT_API_KEY", None), timeout=2.0)
        except Exception:
            self.client = AsyncQdrantClient(":memory:")

    async def ensure_collection(self, name: str, dimension: int):
        try:
            exists = await self.client.collection_exists(name)
            if not exists:
                await self.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
                )
                for field, schema in [
                    ("document_id", models.PayloadSchemaType.KEYWORD),
                    ("document_type", models.PayloadSchemaType.KEYWORD),
                    ("embedding_type", models.PayloadSchemaType.KEYWORD),
                    ("language", models.PayloadSchemaType.KEYWORD),
                    ("embedding_version", models.PayloadSchemaType.KEYWORD),
                ]:
                    try:
                        await self.client.create_payload_index(name, field_name=field, field_schema=schema)
                    except Exception:
                        pass
                logger.info("qdrant_collection_created", name=name, dimension=dimension)
        except Exception as e:
            logger.warning("qdrant_ensure_collection_failed", collection=name, error=str(e))

    async def upsert(self, collection: str, points: list[dict]):
        qdrant_points = [
            models.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points if p.get("vector")
        ]
        if qdrant_points:
            try:
                await self.ensure_collection(collection, len(points[0]["vector"]))
                await self.client.upsert(collection_name=collection, points=qdrant_points)
            except Exception as e:
                logger.warning("qdrant_upsert_failed", collection=collection, error=str(e))

    async def search(self, collection: str, vector: list[float], top_k: int, filters: dict | None = None) -> list[dict]:
        if not vector:
            return []
        qdrant_filter = self._build_filter(filters) if filters else None
        try:
            results = await asyncio.wait_for(
                self.client.query_points(
                    collection_name=collection, query=vector, limit=top_k,
                    query_filter=qdrant_filter, with_payload=True,
                ),
                timeout=2.0
            )
            return [{"id": p.id, "score": p.score, "payload": p.payload} for p in results.points]
        except Exception as e:
            logger.warning("qdrant_search_failed", collection=collection, error=str(e))
            return []

    async def delete(self, collection: str, point_ids: list[str]):
        try:
            await self.client.delete(collection_name=collection, points_selector=models.PointIdsList(points=point_ids))
        except Exception as e:
            logger.warning("qdrant_delete_failed", collection=collection, error=str(e))

    async def get_collection_stats(self, collection: str) -> dict:
        try:
            info = await self.client.get_collection(collection)
            return {"vectors_count": info.vectors_count or 0, "points_count": info.points_count or 0,
                    "status": str(info.status), "segments_count": info.segments_count}
        except Exception:
            return {"vectors_count": 0, "points_count": 0, "status": "offline_fallback", "segments_count": 0}

    async def list_collections(self) -> list[str]:
        try:
            result = await self.client.get_collections()
            return [c.name for c in result.collections]
        except Exception as e:
            logger.warning("qdrant_list_collections_failed", error=str(e))
            return []

    async def delete_collection(self, name: str):
        try:
            await self.client.delete_collection(name)
        except Exception as e:
            logger.warning("qdrant_delete_collection_failed", collection=name, error=str(e))

    def _build_filter(self, filters: dict) -> models.Filter:
        must = []
        for key, value in filters.items():
            if key == "date_range" and isinstance(value, dict):
                gte_val = value.get("gte")
                lte_val = value.get("lte")
                
                if isinstance(gte_val, str):
                    try:
                        from datetime import datetime
                        gte_val = datetime.fromisoformat(gte_val).timestamp()
                    except Exception:
                        gte_val = None
                if isinstance(lte_val, str):
                    try:
                        from datetime import datetime
                        lte_val = datetime.fromisoformat(lte_val).timestamp()
                    except Exception:
                        lte_val = None

                if gte_val is not None or lte_val is not None:
                    must.append(models.FieldCondition(key="processing_timestamp",
                        range=models.Range(gte=gte_val, lte=lte_val)))
            elif isinstance(value, list):
                must.append(models.FieldCondition(key=key, match=models.MatchAny(any=value)))
            elif value is not None:
                must.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))
        return models.Filter(must=must)