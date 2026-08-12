import chromadb

from app.core.config import settings


class VectorService:
    """
    Handles all interactions with ChromaDB.
    """

    def __init__(self):
        # Connect to the ChromaDB server running in Docker.
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )

        # Create the collection if it doesn't exist.
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    def add_document(
        self,
        document_id: str,
        document_text: str,
        embedding: list[float],
        metadata: dict,
    ):
        """
        Stores indexed GitHub knowledge and its metadata inside ChromaDB.
        """

        # Use upsert so repeated indexing updates the stored review in place
        # instead of failing on duplicate IDs during concurrent or retried runs.
        self.collection.upsert(
            ids=[document_id],
            documents=[document_text],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def add_review(
        self,
        review_id: int,
        review_text: str,
        embedding: list[float],
        metadata: dict,
    ):
        """
        Backwards-compatible helper for older review-only callers.
        """

        self.add_document(
            document_id=f"review:{review_id}",
            document_text=review_text,
            embedding=embedding,
            metadata=metadata,
        )

    def search_reviews(
        self,
        query_embedding: list[float],
        repository_id: int | None = None,
        top_k: int = 5,
    ):
        query_arguments = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }

        if repository_id is not None:
            query_arguments["where"] = {"repository_id": repository_id}

        return self.collection.query(
            **query_arguments,
        )

    def document_exists(
        self,
        document_id: str,
    ) -> bool:
        """
        Checks whether a document is already indexed.
        """

        result = self.collection.get(
            ids=[document_id]
        )

        return len(result["ids"]) > 0

    def review_exists(
        self,
        review_id: int,
    ) -> bool:
        """
        Checks whether a review is already indexed.
        """

        return self.document_exists(f"review:{review_id}") or self.document_exists(
            str(review_id)
        )
