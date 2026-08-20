import os
from pathlib import Path

from openai import OpenAI


def read_file(path):
    file_path = Path(path)

    if file_path.exists():
        return file_path.read_text(errors="ignore")

    return f"{path} was not found."


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

Analyze the following pipeline information and generate concise release notes.

PIPELINE CONTEXT:
{context}

TEST LOG:
{test_logs}

TERRAFORM LOG:
{terraform_logs}

Generate Markdown release notes containing:

# AI Release Notes

## Pipeline Status
State whether the pipeline appears successful or failed.

## Changes / Deployment
Summarize what was deployed or prepared for deployment.

## Validation
Summarize the test and Terraform results.

## Docker / ECR
Mention the Docker image and ECR repository information if available.

## AI Summary
Give a short overall assessment.

Do not invent information that is not present in the supplied context or logs.
Keep the response concise and suitable for a software release.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    output = response.output_text

    Path("ai-release-notes.md").write_text(output)

    print("AI release notes generated successfully.")


if __name__ == "__main__":
    main()