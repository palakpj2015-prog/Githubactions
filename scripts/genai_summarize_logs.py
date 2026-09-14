import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")


def read_file(path, max_chars=8000):
    file_path = Path(path)

    if not file_path.exists():
        return f"{path} was not found."

    content = file_path.read_text(errors="ignore")

    if len(content) > max_chars:
        content = content[:max_chars] + "\n[Log truncated]"

    return content


def extract_test_facts(log):
    facts = {
        "failed_test": "Unknown",
        "expected_status": "Unknown",
        "actual_status": "Unknown",
        "endpoint": "/health",
        "test_file": "app/test_main.py",
        "application_file": "app/main.py",
    }

    # Find failed test
    match = re.search(
        r"FAILED\s+.*?::([A-Za-z0-9_]+)",
        log
    )

    if match:
        facts["failed_test"] = match.group(1)

    # Read expected status from test
    test_path = Path(facts["test_file"])

    if test_path.exists():
        test_code = test_path.read_text(errors="ignore")

        match = re.search(
            r"test_health[\s\S]*?assert\s+resp\.status_code\s*==\s*(\d+)",
            test_code
        )

        if match:
            facts["expected_status"] = match.group(1)

    # Read actual status from pytest output
    match = re.search(
        r"assert\s+(\d+)\s*==\s*(\d+)",
        log
    )

    if match:
        facts["actual_status"] = match.group(1)

    if facts["failed_test"] == "test_health":
        facts["endpoint"] = "/health"

    return facts


def call_local_ai(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 500
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
            "Ollama took longer than 5 minutes to generate the AI diagnosis."
        ) from exc

    output = result.get("response", "").strip()

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    return output


def main():
    context = read_file("poc-context.txt", 6000)
    test_logs = read_file("workflow-logs.txt", 7000)
    terraform_logs = read_file("terraform-plan.log", 5000)

    facts = extract_test_facts(test_logs)

    # Pipeline facts
    pipeline_status = "FAILED"
    failed_job = "test"
    terraform_status = "SKIPPED"
    docker_status = "SKIPPED"
    genai_status = "COMPLETED"

    structured_facts = f"""
PIPELINE FACTS

Pipeline status: {pipeline_status}
Failed job: {failed_job}
Failed test: {facts["failed_test"]}

Terraform: {terraform_status}
Docker/ECR: {docker_status}
GenAI: {genai_status}

Endpoint: {facts["endpoint"]}
Expected HTTP status: {facts["expected_status"]}
Actual HTTP status: {facts["actual_status"]}

Application file: {facts["application_file"]}
Test file: {facts["test_file"]}
"""

    prompt = f"""
You are an AI-powered DevOps failure diagnosis assistant.

The following pipeline facts were extracted by Python.

Treat these facts as authoritative.

Do not change, reverse, or invent them.

Expected HTTP status: {facts["expected_status"]}
Actual HTTP status: {facts["actual_status"]}

Failed job: {failed_job}
Failed test: {facts["failed_test"]}

Terraform: {terraform_status}
Docker/ECR: {docker_status}
GenAI: {genai_status}

Do not say GenAI was skipped.
Do not say Terraform or Docker failed.
Do not reverse expected and actual values.

Explain the failure and recommend the correct fix.

If the application returns HTTP 500 while the test expects
HTTP 200, recommend fixing app/main.py instead of changing
the test expectation.

Use only the evidence provided.

PIPELINE FACTS
==============
{structured_facts}

PIPELINE CONTEXT
================
{context}

TEST LOG
========
{test_logs}

TERRAFORM LOG
=============
{terraform_logs}

Return only these sections:

## Root Cause

Explain why the test failed.

## Impact

Explain what the failure affects.

## Recommended Fix

Give the smallest appropriate fix.

For an HTTP 500 returned by app/main.py when the test expects
HTTP 200, recommend changing app/main.py so the /health
endpoint returns HTTP 200.

Do not recommend changing the test expectation.

## Verification Steps

Include:

pytest app/test_main.py::test_health -v

and:

pytest app/ -v

## Preventive Recommendation

Give one or two practical recommendations.

## AI Confidence

Choose exactly one:

High
Medium
Low

Give one short reason.
"""

    ai_reasoning = call_local_ai(prompt)

    report = f"""# AI Failure Diagnosis & Remediation

## Overall Assessment

- Overall pipeline state: {pipeline_status}
- Failed GitHub Actions job: {failed_job}
- Failed test: {facts["failed_test"]}
- Skipped jobs: Terraform Plan, Docker/ECR
- GenAI analysis completed: Yes

## Failure Detection

- Endpoint: {facts["endpoint"]}
- Expected HTTP status: {facts["expected_status"]}
- Actual HTTP status: {facts["actual_status"]}
- Application file: {facts["application_file"]}
- Test file: {facts["test_file"]}

## Evidence

- Test: `{facts["failed_test"]}`
- Endpoint: `{facts["endpoint"]}`
- Expected: `{facts["expected_status"]}`
- Actual: `{facts["actual_status"]}`
- Application: `{facts["application_file"]}`
- Test: `{facts["test_file"]}`

{ai_reasoning}
"""

    Path("ai-log-summary.md").write_text(report)

    print("AI failure diagnosis generated successfully.")
    print()
    print(report)


if __name__ == "__main__":
    main()