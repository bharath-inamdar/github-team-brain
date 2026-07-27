from google import genai

from app.core.config import settings


class AIService:
    """
    A wrapper around the Gemini API.

    Keeping all AI-related code in one place makes it easy
    to swap providers (OpenAI, Anthropic, local models)
    without changing the rest of the application.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def generate_text(self, prompt: str) -> str:
        """
        Sends a prompt to Gemini and returns the generated text.
        """

        response = self.client.models.generate_content(
            model="models/gemini-3.6-flash",
            contents=prompt,
        )

        return response.text

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generates a vector embedding for the given text.
        """

        response = self.client.models.embed_content(
             model="models/gemini-embedding-001",
             contents=text,
        )

        return response.embeddings[0].values

    def answer_question(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Answers a question using the retrieved review context.
        """

        prompt = f"""
You are TeamBrain.

Answer ONLY using the review context below.

If the answer cannot be found,
say that the repository does not contain enough information.

------------------------
Review Context
------------------------

{context}

------------------------
Question
------------------------

{question}
"""

        response = self.client.models.generate_content(
            model="models/gemini-3.6-flash",
            contents=prompt,
        )

        return response.text


