"""Consolidated database clients for chat history and vector stores.

Single import surface for both persistence layers:
- chat database (SQLite/PostgreSQL)
- vector databases (ChromaDB/Qdrant)
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .embeddings import BaseEmbedder


# ── Core domain types ──────────────────────────────────────────────────────────

class Document(BaseModel):
    """A single piece of text content, with optional metadata.
    
    Created by document loaders, consumed by embedders and vector DBs.
    """

    id: Optional[str] = Field(None, description="Unique identifier for the document.")
    content: str = Field(..., description="The text content of the document.")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata associated with the document."
    )


class SearchResult(BaseModel):
    """A retrieved document together with its similarity score."""

    document: Document = Field(..., description="The retrieved document.")
    score: float = Field(..., description="The similarity score of the document to the query.")


# ── Vector DB configuration models ───────────────────────────────────────────

class VectorDBConfig(BaseModel):
    """Base configuration shared by all vector database backends."""

    collection_name: str = Field(..., description="Name of the collection/index.")
    distance_metric: str = Field(
        "COSINE", description="Distance metric for vector similarity (e.g., COSINE, EUCLID)."
    )


class ChromaDBConfig(VectorDBConfig):
    """Configuration for ChromaDB."""

    persist_directory: Optional[str] = Field(
        None, description="Directory to persist ChromaDB data. None = in-memory."
    )


class QdrantDBConfig(VectorDBConfig):
    """Configuration for Qdrant."""

    location: Optional[str] = Field(":memory:", description="':memory:', a local path, or a URL.")
    host: Optional[str] = Field(None, description="Host for a remote Qdrant instance.")
    port: Optional[int] = Field(None, description="Port for a remote Qdrant instance.")
    grpc_port: Optional[int] = Field(None, description="gRPC port for a remote Qdrant instance.")
    api_key: Optional[str] = Field(None, description="API key for Qdrant Cloud.")


# ─────────────────────────────────────────────────────────────────────────────

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConversationRecord:
    id: str
    title: str
    mode: str
    provider: str
    model: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


@dataclass
class MessageRecord:
    id: int
    conversation_id: str
    role: str
    content: str
    created_at: str
    metadata: Dict[str, Any]


class BaseChatStore:
    def initialize(self) -> None:
        raise NotImplementedError

    def create_conversation(
        self,
        *,
        title: str,
        mode: str,
        provider: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationRecord:
        raise NotImplementedError

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageRecord:
        raise NotImplementedError

    def list_conversations(self, limit: int = 50) -> List[ConversationRecord]:
        raise NotImplementedError

    def get_messages(self, conversation_id: str, limit: int = 500) -> List[MessageRecord]:
        raise NotImplementedError


class SQLiteChatStore(BaseChatStore):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
        self.conn.commit()

    def _require_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError("SQLiteChatStore is not initialized. Call initialize() first.")
        return self.conn

    def create_conversation(
        self,
        *,
        title: str,
        mode: str,
        provider: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationRecord:
        conn = self._require_conn()
        now = _utc_now_iso()
        conversation_id = str(uuid.uuid4())
        meta = metadata or {}

        conn.execute(
            """
            INSERT INTO conversations (id, title, mode, provider, model, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, title, mode, provider, model, json.dumps(meta), now, now),
        )
        conn.commit()

        return ConversationRecord(
            id=conversation_id,
            title=title,
            mode=mode,
            provider=provider,
            model=model,
            created_at=now,
            updated_at=now,
            metadata=meta,
        )

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageRecord:
        conn = self._require_conn()
        now = _utc_now_iso()
        meta = metadata or {}

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (conversation_id, role, content, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, role, content, json.dumps(meta), now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        conn.commit()

        return MessageRecord(
            id=cur.lastrowid,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=now,
            metadata=meta,
        )

    def list_conversations(self, limit: int = 50) -> List[ConversationRecord]:
        conn = self._require_conn()
        rows = conn.execute(
            """
            SELECT id, title, mode, provider, model, metadata_json, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            ConversationRecord(
                id=row["id"],
                title=row["title"],
                mode=row["mode"],
                provider=row["provider"],
                model=row["model"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]

    def get_messages(self, conversation_id: str, limit: int = 500) -> List[MessageRecord]:
        conn = self._require_conn()
        rows = conn.execute(
            """
            SELECT id, conversation_id, role, content, metadata_json, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (conversation_id, limit),
        ).fetchall()

        return [
            MessageRecord(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]


class PostgresChatStore(BaseChatStore):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.conn: Any = None

    def initialize(self) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise ImportError("psycopg is required for PostgreSQL chat store. Install with: pip install psycopg") from exc

        self.conn = psycopg.connect(self.dsn)
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
        self.conn.commit()

    def _require_conn(self) -> Any:
        if self.conn is None:
            raise RuntimeError("PostgresChatStore is not initialized. Call initialize() first.")
        return self.conn

    def create_conversation(
        self,
        *,
        title: str,
        mode: str,
        provider: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationRecord:
        conn = self._require_conn()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        conversation_id = str(uuid.uuid4())
        meta = metadata or {}

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversations (id, title, mode, provider, model, metadata_json, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                """,
                (conversation_id, title, mode, provider, model, json.dumps(meta), now, now),
            )
        conn.commit()

        return ConversationRecord(
            id=conversation_id,
            title=title,
            mode=mode,
            provider=provider,
            model=model,
            created_at=now_iso,
            updated_at=now_iso,
            metadata=meta,
        )

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageRecord:
        conn = self._require_conn()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        meta = metadata or {}

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages (conversation_id, role, content, metadata_json, created_at)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                RETURNING id
                """,
                (conversation_id, role, content, json.dumps(meta), now),
            )
            row = cursor.fetchone()
            message_id = row[0]
            cursor.execute("UPDATE conversations SET updated_at = %s WHERE id = %s", (now, conversation_id))
        conn.commit()

        return MessageRecord(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=now_iso,
            metadata=meta,
        )

    def list_conversations(self, limit: int = 50) -> List[ConversationRecord]:
        conn = self._require_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, mode, provider, model, metadata_json::text, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        return [
            ConversationRecord(
                id=row[0],
                title=row[1],
                mode=row[2],
                provider=row[3],
                model=row[4],
                metadata=json.loads(row[5] or "{}"),
                created_at=row[6].isoformat(),
                updated_at=row[7].isoformat(),
            )
            for row in rows
        ]

    def get_messages(self, conversation_id: str, limit: int = 500) -> List[MessageRecord]:
        conn = self._require_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, conversation_id, role, content, metadata_json::text, created_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (conversation_id, limit),
            )
            rows = cursor.fetchall()

        return [
            MessageRecord(
                id=row[0],
                conversation_id=row[1],
                role=row[2],
                content=row[3],
                metadata=json.loads(row[4] or "{}"),
                created_at=row[5].isoformat(),
            )
            for row in rows
        ]


def get_chat_store(
    backend: Optional[str] = None,
    sqlite_path: Optional[str] = None,
    postgres_dsn: Optional[str] = None,
) -> BaseChatStore:
    """Create and initialize a chat store.

    Backend priority:
    1) explicit backend argument
    2) CHAT_DB_BACKEND env var
    3) sqlite default
    """
    backend_key = (backend or os.getenv("CHAT_DB_BACKEND", "sqlite")).strip().lower()

    if backend_key == "sqlite":
        path = sqlite_path or os.getenv("CHAT_DB_PATH", "llm_toolbox/db/chat_database.db")
        store = SQLiteChatStore(path)
        store.initialize()
        return store

    if backend_key in {"postgres", "postgresql"}:
        dsn = postgres_dsn or os.getenv("CHAT_DB_DSN")
        if not dsn:
            raise ValueError("CHAT_DB_DSN is required when CHAT_DB_BACKEND=postgres")
        store = PostgresChatStore(dsn)
        store.initialize()
        return store

    raise ValueError(f"Unsupported chat DB backend: {backend_key}")


class BaseVectorDB(ABC):
    """Abstract base class for vector database integrations."""

    def __init__(self, config: Any, embedder: Any):
        self.config = config
        self.embedder = embedder
        self.collection = None

    @abstractmethod
    def create_collection(self):
        raise NotImplementedError

    @abstractmethod
    def add_documents(self, documents: List[Any]):
        raise NotImplementedError

    @abstractmethod
    def search(self, query_text: str, limit: int = 5) -> List[Any]:
        raise NotImplementedError


class ChromaDB(BaseVectorDB):
    """Vector database integration for ChromaDB."""

    def __init__(self, config: Any, embedder: Any):
        super().__init__(config, embedder)
        try:
            import chromadb
        except ImportError as exc:
            raise ImportError("chromadb is required for ChromaDB support. Install with: pip install chromadb") from exc

        self._chromadb = chromadb
        self.client = chromadb.Client(
            chromadb.config.Settings(
                persist_directory=config.persist_directory,
            )
        ) if config.persist_directory else chromadb.Client()
        self.create_collection()

    def create_collection(self):
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self._chroma_embedding_function(),
        )
        print(f"ChromaDB collection '{self.config.collection_name}' ready.")

    def _chroma_embedding_function(self):
        Document, _, _, _, _ = _get_model_types()

        class ChromaEmbeddingFunction:
            def __init__(self, embedder: Any):
                self._embedder = embedder

            def __call__(self, input: List[str]) -> List[List[float]]:
                docs = [Document(content=text) for text in input]
                return self._embedder.embed_documents(docs)

        return ChromaEmbeddingFunction(self.embedder)

    def add_documents(self, documents: List[Any]):
        if not self.collection:
            self.create_collection()

        ids = [doc.id if getattr(doc, "id", None) else str(uuid.uuid4()) for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata if getattr(doc, "metadata", None) else {} for doc in documents]

        try:
            self.collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=ids,
            )
            print(f"Added {len(documents)} documents to ChromaDB collection '{self.config.collection_name}'.")
        except Exception as exc:
            print(f"Error adding documents to ChromaDB: {exc}")

    def search(self, query_text: str, limit: int = 5) -> List[Any]:
        Document, SearchResult, _, _, _ = _get_model_types()

        if not self.collection:
            print("ChromaDB collection not initialized. Please call create_collection first.")
            return []

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                include=["documents", "distances", "metadatas", "ids"],
            )

            search_results = []
            if results and results["documents"] and results["distances"]:
                for i in range(len(results["documents"][0])):
                    doc_content = results["documents"][0][i]
                    doc_id = results["ids"][0][i]
                    doc_metadata = results["metadatas"][0][i]
                    score = results["distances"][0][i]

                    document = Document(id=doc_id, content=doc_content, metadata=doc_metadata)
                    search_results.append(SearchResult(document=document, score=score))
            print(f"Found {len(search_results)} results in ChromaDB.")
            return search_results
        except Exception as exc:
            print(f"Error searching ChromaDB: {exc}")
            return []

    def backup(self, backup_path: str) -> str:
        persist_dir = self.config.persist_directory
        if not persist_dir or not os.path.exists(persist_dir):
            raise FileNotFoundError(f"Persist directory '{persist_dir}' not found.")
        zip_base = backup_path.rstrip(".zip")
        shutil.make_archive(zip_base, "zip", persist_dir)
        zip_path = f"{zip_base}.zip"
        print(f"ChromaDB backed up to {zip_path}")
        return zip_path

    def restore(self, zip_path: str) -> None:
        persist_dir = self.config.persist_directory
        if not persist_dir:
            raise ValueError("ChromaDBConfig.persist_directory must be set to restore.")
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Backup zip '{zip_path}' not found.")
        shutil.unpack_archive(zip_path, persist_dir, "zip")
        print(f"ChromaDB restored from {zip_path} to {persist_dir}")
        self.client = self._chromadb.PersistentClient(path=persist_dir)
        self.create_collection()

    def delete(self, *, backup_first: bool = True, backup_path: str | None = None) -> None:
        persist_dir = self.config.persist_directory
        if backup_first:
            dest = backup_path or persist_dir
            self.backup(dest)
        if self.collection:
            self.client.delete_collection(self.config.collection_name)
            print(f"Collection '{self.config.collection_name}' deleted.")
        if persist_dir and os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            print(f"Persist directory '{persist_dir}' removed.")


class QdrantDB(BaseVectorDB):
    """Vector database integration for Qdrant."""

    def __init__(self, config: Any, embedder: Any):
        super().__init__(config, embedder)
        try:
            from qdrant_client import QdrantClient, models as qdrant_models
        except ImportError as exc:
            raise ImportError("qdrant-client is required for Qdrant support. Install with: pip install qdrant-client") from exc

        self._qdrant_models = qdrant_models
        if config.location == ":memory:":
            self.client = QdrantClient(location=config.location)
        elif config.host:
            self.client = QdrantClient(
                host=config.host,
                port=config.port,
                grpc_port=config.grpc_port,
                api_key=config.api_key,
            )
        else:
            raise ValueError("QdrantDBConfig must specify either 'location' (for in-memory/local) or 'host' (for remote).")

        self.create_collection()

    def create_collection(self):
        try:
            collection_exists = self.client.collection_exists(collection_name=self.config.collection_name)

            if collection_exists:
                print(f"Qdrant collection '{self.config.collection_name}' already exists. Deleting and recreating.")
                self.client.delete_collection(collection_name=self.config.collection_name)

            self.client.recreate_collection(
                collection_name=self.config.collection_name,
                vectors_config=self._qdrant_models.VectorParams(
                    size=self.embedder.config.vector_size,
                    distance=self._qdrant_models.Distance[self.config.distance_metric.upper()],
                ),
            )
            print(f"Qdrant collection '{self.config.collection_name}' created/recreated.")
        except Exception as exc:
            print(f"Error creating/recreating Qdrant collection: {exc}")

    def add_documents(self, documents: List[Any]):
        points = []
        for doc in documents:
            doc_id = doc.id if getattr(doc, "id", None) else str(uuid.uuid4())
            embedding = self.embedder.embed_documents([doc])[0]
            points.append(
                self._qdrant_models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=doc.model_dump(exclude_none=True),
                )
            )
        try:
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=points,
                wait=True,
            )
            print(f"Added {len(documents)} documents to Qdrant collection '{self.config.collection_name}'.")
        except Exception as exc:
            print(f"Error adding documents to Qdrant: {exc}")

    def search(self, query_text: str, limit: int = 5) -> List[Any]:
        Document, SearchResult, _, _, _ = _get_model_types()
        try:
            query_vector = self.embedder.embed_query(query_text)
            hits = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_vector,
                limit=limit,
            )

            search_results = []
            for hit in hits:
                doc_data = hit.payload
                document = Document(**doc_data)
                search_results.append(SearchResult(document=document, score=hit.score))
            print(f"Found {len(search_results)} results in Qdrant.")
            return search_results
        except Exception as exc:
            print(f"Error searching Qdrant: {exc}")
            return []


__all__ = [
    "BaseChatStore",
    "ConversationRecord",
    "MessageRecord",
    "PostgresChatStore",
    "SQLiteChatStore",
    "get_chat_store",
    "BaseVectorDB",
    "ChromaDB",
    "QdrantDB",
]
