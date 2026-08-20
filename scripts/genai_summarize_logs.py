import json
import os
import urllib.request
from pathlib import Path


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")


def read_file(path, max_chars=12000):
    file_path = Path(path)

    if not file_path.exists():
        return f"{path} was not found."

    content = file_path.read_text(errors="ignore")

    if len(content) > max_chars:
        content = content[:max_chars] + "\n[Log truncated]"

    return content


def call_local_ai(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result.get("response", "").strip()


def main():
    context = read_file("poc-context.txt")
    test_logs = read_file("workflow-logs.txt")
    terraform_logs = read_file("terraform-plan.log")

    prompt = f"""
You are a DevOps AI assistant integrated into GitHub Actions.

Analyze the CI/CD pipeline information below and produce a concise,
human-readable pipeline analysis.

PIPELINE CONTEXT:
{context}

TEST LOG:
{test_logs}

TERRAFORM LOG:
{terraform_logs}

Generate Markdown with exactly these sections:

# AI Pipeline Log Summary

## Pipeline Status
Explain whether the pipeline stages appear successful or failed.

## Test Analysis
Summarize the application test results.

## Terraform Analysis
Summarize the Terraform validation and plan results.

## Issues Detected
List important errors, warnings, or potential problems.
If there are none, explicitly state that no significant issues were detected.

## Recommendations
Provide practical recommendations only when appropriate.

Rules:
- Base the analysis only on the supplied context and logs.
- Do not invent information.
- Keep the summary concise.
- Highlight actionable problems.
"""

    output = call_local_ai(prompt)

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    Path("ai-log-summary.md").write_text(output)

    print("AI log summary generated successfully.")


if __name__ == "__main__":
    main()