
# ===== app/vectorstore/qdrant_provider.py =====
from qdrant_client import AsyncQdrantClient, models
from app.vectorstore.base import VectorStoreProvider
from app.core.config import settings
from app.core.logging_config import logger

class QdrantProvider(VectorStoreProvider):
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=getattr(settings, "QDRANT_API_KEY", None))

    async def ensure_collection(self, name: str, dimension: int):
        exists = await self.client.collection_exists(name)
        if not exists:
            await self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )
            # payload indexes for common filter fields — speeds up filtered search
            for field, schema in [
                ("document_id", models.PayloadSchemaType.KEYWORD),
                ("document_type", models.PayloadSchemaType.KEYWORD),
                ("embedding_type", models.PayloadSchemaType.KEYWORD),
                ("language", models.PayloadSchemaType.KEYWORD),
                ("embedding_version", models.PayloadSchemaType.KEYWORD),
            ]:
                await self.client.create_payload_index(name, field_name=field, field_schema=schema)
            logger.info("qdrant_collection_created", name=name, dimension=dimension)

    async def upsert(self, collection: str, points: list[dict]):
        qdrant_points = [
            models.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points if p.get("vector")
        ]
        if qdrant_points:
            await self.client.upsert(collection_name=collection, points=qdrant_points)

    
    async def search(self, collection: str, vector: list[float], top_k: int, filters: dict | None = None) -> list[dict]:
        qdrant_filter = self._build_filter(filters) if filters else None
        results = await self.client.query_points(
            collection_name=collection, query=vector, limit=top_k,
            query_filter=qdrant_filter, with_payload=True,
        )
        return [{"id": p.id, "score": p.score, "payload": p.payload} for p in results.points]
    async def delete(self, collection: str, point_ids: list[str]):
        await self.client.delete(collection_name=collection, points_selector=models.PointIdsList(points=point_ids))

    async def get_collection_stats(self, collection: str) -> dict:
        try:
            info = await self.client.get_collection(collection)
            return {"vectors_count": info.vectors_count or 0, "points_count": info.points_count or 0,
                    "status": str(info.status), "segments_count": info.segments_count}
        except Exception:
            return {"vectors_count": 0, "points_count": 0, "status": "not_found", "segments_count": 0}

    async def list_collections(self) -> list[str]:
        result = await self.client.get_collections()
        return [c.name for c in result.collections]

    async def delete_collection(self, name: str):
        await self.client.delete_collection(name)

    def _build_filter(self, filters: dict) -> models.Filter:
        must = []
        for key, value in filters.items():
            if key == "date_range" and isinstance(value, dict):
                must.append(models.FieldCondition(key="processing_timestamp",
                    range=models.Range(gte=value.get("gte"), lte=value.get("lte"))))
            elif isinstance(value, list):
                must.append(models.FieldCondition(key=key, match=models.MatchAny(any=value)))
            else:
                must.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))
        return models.Filter(must=must)