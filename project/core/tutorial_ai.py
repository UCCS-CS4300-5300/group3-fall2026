import os
from pathlib import Path
from django.contrib.staticfiles import finders

import ollama


MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")

TUTORIAL_DIR = Path(__file__).resolve().parent / "tutorials"


# this is where more tutorials will be added as lessons expand
AVAILABLE_TUTORIALS = {
    "conditionals": "conditionals.md",
}


def load_room_tutorial(room):
    """Load the Markdown document associated with a room."""
    relative_path = Path(room.tutorial_document_path)

    # Only allow Markdown files inside the tutorials directory.
    if (
        relative_path.is_absolute()
        or relative_path.parts[:1] != ("tutorials",)
        or ".." in relative_path.parts
        or relative_path.suffix.lower() != ".md"
    ):
        raise ValueError("Invalid tutorial document path.")

    # Find the tutorial in Django's configured static directories.
    found_path = finders.find(relative_path.as_posix())

    if found_path is None:
        raise FileNotFoundError("Tutorial document not found.")

    # Read the Markdown document.
    document_path = Path(found_path).resolve()
    return document_path.read_text(encoding="utf-8")


def ask_tutor_with_document(document, question, client=None):
    "Answers a question using the tutorial content"
    client = client or ollama.Client()


    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a beginner programming tutor for Code Blocks. "
                    "Use the provided tutorial document to answer the student's question. "
                    "Only reference blocks available in the lesson. "
                    "Use specific examples from the tutorial document when explaining concepts. "
                    "Keep answers concise, 2-4 sentences unless directed otherwise."
                    "Provide hints before revealing complete solutions.\n\n"
                    f"Tutorial document:\n{document}"
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ]
    )

    return response.message.content