from google import genai
from google.genai import types

from app.core.config import settings


class AIService:
    """
    Wrapper around the Gemini API.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = "models/gemini-3.6-flash"

    def generate_text(self, prompt: str) -> str:
        """
        Generate text using Gemini.
        """

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=700,
            ),
        )

        return response.text

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for the given text.
        """

        response = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )

        return response.embeddings[0].values

    def answer_question(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Answer a repository question using retrieved review context.
        """

        prompt = f"""
You are TeamBrain.

Answer the question using ONLY the review comments below.

If the answer cannot be determined from the review comments,
say:

"The repository does not contain enough information."

Review Comments:

{context}

Question:

{question}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=800,
            ),
        )

        return response.text

    def summarize_repository(
        self,
        context: str,
    ) -> str:
        """
        Generate a repository engineering summary.
        """

        prompt = f"""
You are a senior software engineer.

Below are pull request review comments.

Summarise them as a Markdown report.

Only use information that appears in the review comments.

Use the following headings:

# Repository Engineering Summary

## Common Coding Practices

## Frequently Discussed Topics

## Architecture Patterns

## Code Quality Observations

If a section has no evidence, write:

- No significant observations.

Review comments:

{context}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=700,
            ),
        )

        print("\n========== GEMINI RAW RESPONSE ==========\n")
        print(response.text)
        print("\n=========================================\n")

        return response.text