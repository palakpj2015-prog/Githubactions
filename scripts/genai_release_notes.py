import json
import os
import urllib.error
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

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to connect to local Ollama service: {exc}"
        ) from exc

    output = result.get("response", "").strip()

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    return output


def main():
    context = read_file("poc-context.txt")
    test_logs = read_file("workflow-logs.txt")
    terraform_logs = read_file("terraform-plan.log")

    prompt = f"""
You are a DevOps AI assistant integrated into a GitHub Actions
CI/CD pipeline.

Create concise release notes based ONLY on the supplied pipeline
context and logs.

PIPELINE CONTEXT
================
{context}

TEST LOG
========
{test_logs}

TERRAFORM LOG
=============
{terraform_logs}

Generate Markdown using EXACTLY these sections:

# AI Release Notes

## Pipeline Status

State whether the pipeline appears:

- Successful
- Failed
- Partially successful
- Blocked/skipped

## Changes & Validation

Summarize what was tested, validated, built, or planned.

Do not claim that infrastructure was actually deployed unless
the logs prove that an apply/deployment occurred.

## Docker & ECR

Summarize the Docker/ECR activity shown by the available context.

Mention the repository and image tag when available.

## Infrastructure

Summarize the Terraform activity.

Clearly distinguish between:

- validation
- plan
- apply

Do not describe a plan as an actual deployment.

## Security & Quality

Mention relevant test, Semgrep, tfsec, or infrastructure
security information only when available in the supplied data.

## AI Summary

Give a short professional assessment of the pipeline.

Rules:

- Use only supplied information.
- Do not invent changes.
- Do not invent deployment results.
- Keep the output concise.
- Use professional DevOps terminology.
"""


    output = call_local_ai(prompt)

    Path("ai-release-notes.md").write_text(output)

    print("AI release notes generated successfully.")
    print()
    print(output)


if __name__ == "__main__":
    main()