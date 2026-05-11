import json
import asyncio
import logging
from pathlib import Path
from backend.core.config import settings

logger = logging.getLogger(__name__)

class MedicalVectorStore:
    COLLECTION_NAME = "pubmed_medical"
    CHUNK_SIZE = 256
    CHUNK_OVERLAP = 32
    BATCH_SIZE = 100
    
    def __init__(self):
        self._client = None
        self._collection = None
        self._embedder = None
        
    async def initialize(self):
        import chromadb
        persist_path = settings.MODEL_CACHE_DIR / "chromadb"
        persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_path))
            
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        
        doc_count = self._collection.count()
        logger.info(f"ChromaDB initialized. Documents: {doc_count}")
        
        if doc_count == 0:
            logger.info("ChromaDB is empty. Starting PubMed ingestion...")
            await asyncio.to_thread(self.ingest_from_json, Path("data/pubmed_raw.json"))

    def ingest_from_json(self, json_path: Path):
        if not json_path.exists():
            logger.warning(f"PubMed data file not found: {json_path}. RAG will be limited.")
            return
            
        records = json.loads(json_path.read_text(encoding="utf-8"))
        logger.info(f"Ingesting {len(records)} PubMed records into ChromaDB...")
        
        all_chunks, all_ids, all_metadatas = [], [], []
        
        for record in records:
            if not record.get("abstract"): continue
            text = f"{record['title']}. {record['abstract']}"
            chunks = self._chunk_text(text, self.CHUNK_SIZE, self.CHUNK_OVERLAP)
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"{record['pmid']}_chunk_{i}")
                all_metadatas.append({
                    "pmid": str(record["pmid"]),
                    "title": record["title"][:200],
                    "disease_category": record.get("category", "general"),
                    "year": str(record.get("year", ""))
                })
                
        embedder = self._get_embedder()
        
        for i in range(0, len(all_chunks), self.BATCH_SIZE):
            batch_chunks = all_chunks[i:i+self.BATCH_SIZE]
            batch_ids = all_ids[i:i+self.BATCH_SIZE]
            batch_metas = all_metadatas[i:i+self.BATCH_SIZE]
            
            embeddings = embedder.encode(batch_chunks, show_progress_bar=False).tolist()
            self._collection.add(documents=batch_chunks, embeddings=embeddings, ids=batch_ids, metadatas=batch_metas)
            
        logger.info(f"Ingestion complete. Total documents: {self._collection.count()}")

    def search(self, query: str, n_results: int = 5, disease_filter: str = None) -> list[dict]:
        if not self._collection: return []
        embedder = self._get_embedder()
        query_embedding = embedder.encode([query])[0].tolist()
        
        where_filter = {"disease_category": disease_filter} if disease_filter else None
        
        results = self._collection.query(
            query_embeddings=[query_embedding], n_results=n_results,
            where=where_filter, include=["documents", "metadatas", "distances"]
        )
        
        output = []
        if results["documents"]:
            for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
                relevance = float(1 - dist)
                output.append({
                    "text": doc, "pmid": meta.get("pmid", ""), "title": meta.get("title", ""),
                    "disease_category": meta.get("disease_category", ""), "year": meta.get("year", ""),
                    "relevance_score": round(max(0, relevance), 3)
                })
        return output

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        words = text.split()
        chunks, start = [], 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            start = end - overlap
            if start >= len(words): break
        return chunks

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            cache_dir = str(settings.MODEL_CACHE_DIR / "minilm")
            self._embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", cache_folder=cache_dir)
        return self._embedder

vector_store = MedicalVectorStore()
