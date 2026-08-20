#!/usr/bin/env python3
"""Generate AI release notes from CI/CD context."""
import json
import os
from pathlib import Path
from urllib import request


def call_openai(prompt: str) -> str:
    body = json.dumps(
        {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Write concise CI/CD release notes in markdown. "
                        "Do not invent test results or deployment outcomes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode()

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def main() -> None:
    context_path = Path("poc-context.txt")
    context = context_path.read_text(encoding="utf-8") if context_path.exists() else "No context provided"

    notes = call_openai(
        "Create release notes with sections: Summary, Changes, CI Status, "
        "Deployment Notes, and Review Items.\n\n"
        + context
    )

    Path("ai-release-notes.md").write_text(notes, encoding="utf-8")
    print("Wrote ai-release-notes.md")


if __name__ == "__main__":
    main()
