import os
from pathlib import Path 

import ollama


MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")

TUTORIAL_DIR = Path(__file__).resolve().parent / "tutorials"


# this is where more tutorials will be added as lessons expand 
AVAILABLE_TUTORIALS = { 
    "conditionals": "conditionals.md",
}

def load_tutorial(topic):
    if topic not in AVAILABLE_TUTORIALS:
        raise ValueError(f"Unknown tutorial: {topic}")

    tutorial_path = TUTORIAL_DIR / AVAILABLE_TUTORIALS[topic]

    return tutorial_path.read_text(encoding="utf-8")

def ask_tutor(topic, question, client=None):
    lesson = load_tutorial(topic)
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
                    "Provide hints before revealing complete solutions.\n\n"
                    f"Tutorial document:\n{lesson}"
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ]
    )

    return response.message.content