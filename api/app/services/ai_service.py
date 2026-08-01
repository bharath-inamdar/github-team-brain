import logging

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Wrapper around the Gemini API.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_model
        self.embedding_model = settings.gemini_embedding_model

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
            model=self.embedding_model,
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

If the answer cannot be determined from the review comments, reply exactly:

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
                max_output_tokens=900,
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
You are a Staff Software Engineer reviewing a large GitHub repository.

You are given ONLY pull request review comments.

Your task is to identify recurring engineering patterns, coding standards,
architecture decisions, review culture, and development practices.

IMPORTANT RULES

- Do NOT invent information.
- Only include findings supported by MULTIPLE review comments.
- Ignore one-off comments.
- If there is insufficient evidence, explicitly say so.
- Focus on repository-wide engineering practices, not individual pull requests.
- Merge similar observations together instead of repeating them.

Return the report in Markdown using EXACTLY this structure.

# Repository Engineering Summary

## Overall Review Culture
Describe how reviewers generally communicate.
Examples:
- collaborative
- strict
- performance-focused
- detail-oriented
- beginner-friendly

## Common Coding Practices
- List recurring coding conventions such as:
- naming conventions
- typing
- validation
- exception handling
- logging
- testing
- documentation
- formatting

## Architecture & Design Patterns
Mention recurring architectural discussions such as:
- dependency injection
- modularization
- service layer
- repository pattern
- API design
- async programming
- caching
- database design

## Frequently Requested Improvements
Summarize what reviewers repeatedly ask contributors to improve.

## Common Bugs or Mistakes
List mistakes reviewers frequently catch.

## Testing Practices
Describe recurring expectations around testing.

## Code Quality Observations
Summarize the overall quality of the repository based only on review comments.

## Key Takeaways
Provide 5 concise bullet points describing the engineering culture.

Review Comments:

{context}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1500,
            ),
        )

        logger.info("Generated repository summary")

        return response.text