
import os
from pathlib import Path

from django.contrib.staticfiles import finders
from groq import Groq


MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")


def load_room_tutorial(room):
    """Load the Markdown document associated with a room."""
    relative_path = Path(room.tutorial_document_path)

    if (
        relative_path.is_absolute()
        or relative_path.parts[:1] != ("tutorials",)
        or ".." in relative_path.parts
        or relative_path.suffix.lower() != ".md"
    ):
        raise ValueError("Invalid tutorial document path.")

    found_path = finders.find(relative_path.as_posix())

    if found_path is None:
        raise FileNotFoundError("Tutorial document not found.")

    document_path = Path(found_path).resolve()
    return document_path.read_text(encoding="utf-8")


def ask_tutor_with_document(document, question, client=None):
    """Answer a question using the current room's tutorial content."""
    client = client if client is not None else Groq(
        api_key=os.environ["GROQ_API_KEY"]
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a beginner programming tutor for Rise of the Dev. "
                    "Use the provided tutorial document to answer the student's question. "
                    "Only reference blocks available in the lesson. "
                    "Use specific examples from the tutorial document when explaining concepts. "
                    "Keep answers concise, 2-4 sentences unless directed otherwise. "
                    "Provide hints before revealing complete solutions.\n\n"
                    f"Tutorial document:\n{document}"
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=0.3,
        max_tokens=350,
    )

    return response.choices[0].message.content or ""
