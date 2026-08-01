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

    def add_review(
        self,
        review_id: int,
        review_text: str,
        embedding: list[float],
        metadata: dict,
    ):
        """
        Stores a pull request review, its embedding,
        and metadata inside ChromaDB.
        """

        self.collection.add(
            ids=[str(review_id)],
            documents=[review_text],
            embeddings=[embedding],
            metadatas=[metadata],
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

    def review_exists(
        self,
        review_id: int,
    ) -> bool:
        """
        Checks whether a review is already indexed.
        """

        result = self.collection.get(
            ids=[str(review_id)]
        )

        return len(result["ids"]) > 0
