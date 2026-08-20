#!/usr/bin/env python3
"""Summarize CI/CD workflow logs using OpenAI."""
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
                        "Summarize CI/CD logs clearly. Highlight failures, warnings, "
                        "and recommended next steps."
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
    logs = ""
    log_path = Path("workflow-logs.txt")
    if log_path.exists():
        logs = log_path.read_text(encoding="utf-8")[:12000]

    summary = call_openai(
        "Summarize these workflow logs:\n\n" + (logs or "No logs captured.")
    )

    Path("ai-log-summary.md").write_text(summary, encoding="utf-8")
    print("Wrote ai-log-summary.md")


if __name__ == "__main__":
    main()
