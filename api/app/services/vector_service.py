import chromadb


class VectorService:
    """
    Handles all interactions with ChromaDB.
    """

    def __init__(self):
        # Connect to the ChromaDB server running in Docker.
        self.client = chromadb.HttpClient(
            host="localhost",
            port=8001,
        )

        # Create the collection if it doesn't exist.
        self.collection = self.client.get_or_create_collection(
            name="teambrain"
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
        repository_id: int,
        top_k: int = 5,
    ):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={
                "repository_id": repository_id,
            },
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