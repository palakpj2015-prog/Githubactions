import os
from pathlib import Path

from openai import OpenAI


MODEL = "gpt-5.6-luna"


def read_file(path, max_chars=12000):
    file_path = Path(path)

    if not file_path.exists():
        return f"{path} was not found."

    content = file_path.read_text(errors="ignore")

    if len(content) > max_chars:
        content = content[:max_chars] + "\n[Log truncated]"

    return content


def main():
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)

    context = read_file("poc-context.txt")
    test_logs = read_file("workflow-logs.txt")
    terraform_logs = read_file("terraform-plan.log")

    prompt = f"""
You are a DevOps AI assistant integrated into a GitHub Actions CI/CD pipeline.

Analyze the pipeline information below and generate concise Markdown
release notes.

PIPELINE CONTEXT:
{context}

TEST LOG:
{test_logs}

TERRAFORM LOG:
{terraform_logs}

Generate the following sections:

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
Provide a concise overall assessment.

Rules:
- Use only information provided above.
- Do not invent deployment details.
- Keep the release notes concise.
- Use professional DevOps terminology.
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    output = response.output_text.strip()

    Path("ai-release-notes.md").write_text(output)

    print("AI release notes generated successfully.")


if __name__ == "__main__":
    main()