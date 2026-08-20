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
You are a DevOps AI assistant integrated into GitHub Actions.

Analyze the CI/CD pipeline logs below and produce a concise,
human-readable troubleshooting and execution summary.

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
Summarize the Terraform validation/plan results.

## Issues Detected
List important errors, warnings, or potential problems.
If there are none, explicitly say so.

## Recommendations
Provide practical next steps only when appropriate.

Do not invent information.
Base the analysis only on the supplied pipeline context and logs.
Keep the response concise.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    output = response.output_text

    Path("ai-log-summary.md").write_text(output)

    print("AI log summary generated successfully.")


if __name__ == "__main__":
    main()