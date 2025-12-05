import os
import redis
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, before_log

from config.settings import settings
from app.models.database import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.postgres_engine = None
        self.SessionLocal = None
        self.qdrant_client = None
        self.neo4j_driver = None
        self.redis_client = None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        before=before_log(logger, logging.INFO)
    )
    def connect_postgres(self):
        """Connect to PostgreSQL with retries."""
        try:
            self.postgres_engine = create_engine(settings.postgres_url)
            self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.postgres_engine))
            
            # Verify connection
            with self.postgres_engine.connect() as connection:
                pass
                
            # Create tables
            Base.metadata.create_all(bind=self.postgres_engine)
            logger.info("✅ PostgreSQL connected and tables created.")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        before=before_log(logger, logging.INFO)
    )
    def connect_qdrant(self):
        """Connect to Qdrant with retries."""
        try:
            self.qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
            # Verify connection (simple call)
            self.qdrant_client.get_collections()
            logger.info("✅ Qdrant connected.")
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        before=before_log(logger, logging.INFO)
    )
    def connect_neo4j(self):
        """Connect to Neo4j with retries."""
        try:
            self.neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            self.neo4j_driver.verify_connectivity()
            logger.info("✅ Neo4j connected.")
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        before=before_log(logger, logging.INFO)
    )
    def connect_redis(self):
        """Connect to Redis with retries."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis connected.")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise e

    def connect_all(self):
        """Initialize all database connections."""
        try:
            self.connect_postgres()
        except Exception:
            logger.warning("⚠️ PostgreSQL initialization failed - continuing without structured DB")
            
        try:
            self.connect_qdrant()
        except Exception:
            logger.warning("⚠️ Qdrant initialization failed - continuing without vector DB")
            
        try:
            self.connect_neo4j()
        except Exception:
            logger.warning("⚠️ Neo4j initialization failed - continuing without graph DB")
            
        try:
            self.connect_redis()
        except Exception:
            logger.warning("⚠️ Redis initialization failed - continuing without cache")

    def get_db(self):
        """Get SQLAlchemy database session."""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def close_connections(self):
        """Close all connections."""
        if self.postgres_engine:
            self.postgres_engine.dispose()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.redis_client:
            self.redis_client.close()
        logger.info("Database connections closed successfully")

    # Alias for backward compatibility
    close_all = close_connections

    def search_vectors(self, collection_name, query_vector, limit=10, score_threshold=0.7):
        """Search vectors in Qdrant"""
        if not self.qdrant_client:
            return []
        try:
            results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            return [
                {"id": hit.id, "score": hit.score, "payload": hit.payload}
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def find_connections(self, phone_number, depth=2):
        """Find connections in Neo4j"""
        if not self.neo4j_driver:
            return []
        query = """
        MATCH (p:Person {phone_number: $phone})
        CALL apoc.path.subgraphAll(p, {maxLevel: $depth})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query, phone=phone_number, depth=depth)
                return result.data()
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
            
    def clear_cache(self):
        """Clear Redis cache"""
        if self.redis_client:
            return self.redis_client.flushall()
        return False
        
    def ping_redis(self):
        """Ping Redis"""
        if self.redis_client:
            return self.redis_client.ping()
        return False

    def get_cached_result(self, key: str):
        """Get a value from Redis cache."""
        if not self.redis_client:
            return None
        try:
            val = self.redis_client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None

    def set_cached_result(self, key: str, value: dict, expire: int = 3600):
        """Set a value in Redis cache."""
        if not self.redis_client:
            return
        try:
            self.redis_client.setex(key, expire, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis set failed: {e}")

    # Alias for backward compatibility with ai_service.py
    def cache_query_result(self, key: str, value: dict, ttl: int = 3600):
        """Alias for set_cached_result to support legacy calls."""
        return self.set_cached_result(key, value, ttl)

db_manager = DatabaseManager()