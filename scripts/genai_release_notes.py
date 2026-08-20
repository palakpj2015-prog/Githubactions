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
You are a DevOps AI assistant integrated into a GitHub Actions CI/CD pipeline.

Analyze the following pipeline information and generate concise release notes.

PIPELINE CONTEXT:
{context}

TEST LOG:
{test_logs}

TERRAFORM LOG:
{terraform_logs}

Generate Markdown using these sections:

# AI Release Notes

## Pipeline Status
State whether the pipeline appears successful, failed, or partially successful.

## Changes / Deployment
Summarize what the pipeline built, validated, or deployed.

## Validation
Summarize the application test and Terraform results.

## Docker / ECR
Summarize the Docker image and ECR information available in the context.

## AI Summary
Provide a short overall assessment.

Rules:
- Use only information provided above.
- Do not invent deployment details.
- Keep the release notes concise.
- Use professional DevOps terminology.
"""

    output = call_local_ai(prompt)

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    Path("ai-release-notes.md").write_text(output)

    print("AI release notes generated successfully.")


if __name__ == "__main__":
    main()