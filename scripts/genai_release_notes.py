import json
import os
import urllib.error
import urllib.request
from pathlib import Path


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")


def read_file(path, max_chars=6000):
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
            "temperature": 0.1,
            "num_predict": 350
        }
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to connect to local Ollama service: {exc}"
        ) from exc

    except TimeoutError as exc:
        raise RuntimeError(
            "Ollama took longer than 5 minutes to generate the release notes."
        ) from exc

    output = result.get("response", "").strip()

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    return output


def main():
    context = read_file("poc-context.txt", 5000)
    test_logs = read_file("workflow-logs.txt", 5000)
    terraform_logs = read_file("terraform-plan.log", 5000)

    prompt = f"""
You are a DevOps AI assistant.

Create SHORT release notes from the pipeline information below.

Do not invent information.
Do not claim deployment unless the logs prove deployment occurred.

PIPELINE:
{context}

TEST LOG:
{test_logs}

TERRAFORM:
{terraform_logs}

Return Markdown with these sections:

# AI Release Notes

## Pipeline Status
State whether the pipeline is successful, failed, partially successful, or blocked.

## Validation
Briefly summarize tests, Terraform validation/plan, Docker and ECR activity.

## Security
Mention relevant security or quality checks if present.

## AI Summary
Give a concise overall assessment.

Keep the response under approximately 300 words.
"""

    output = call_local_ai(prompt)

    Path("ai-release-notes.md").write_text(output)

    print("AI release notes generated successfully.")
    print()
    print(output)


if __name__ == "__main__":
    main()