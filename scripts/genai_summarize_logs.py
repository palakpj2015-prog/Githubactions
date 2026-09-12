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

    # Find failed test name
    match = re.search(
        r"FAILED\s+.*?::([A-Za-z0-9_]+)",
        log
    )

    if match:
        facts["failed_test"] = match.group(1)

    # Find assertion such as:
    # assert 200 == 500
    match = re.search(
        r"assert\s+(\d+)\s*==\s*(\d+)",
        log
    )

    if match:
        facts["expected_status"] = match.group(1)
        facts["actual_status"] = match.group(2)

    # Pytest may also print:
    # E       assert 200 == 500
    match = re.search(
        r"E\s+assert\s+(\d+)\s*==\s*(\d+)",
        log
    )

    if match:
        facts["expected_status"] = match.group(1)
        facts["actual_status"] = match.group(2)

    # Identify endpoint from the test name
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

    test_facts = extract_test_facts(test_logs)

    structured_facts = f"""
STRUCTURED PIPELINE FACTS
=========================

Overall pipeline status:
FAILED

Test job:
FAILED

Terraform job:
SKIPPED

Docker/ECR job:
SKIPPED

GenAI job:
RUNNING

Failed test:
{test_facts["failed_test"]}

Endpoint:
{test_facts["endpoint"]}

Test file:
{test_facts["test_file"]}

Application file:
{test_facts["application_file"]}

Expected HTTP status:
{test_facts["expected_status"]}

Actual HTTP status:
{test_facts["actual_status"]}
"""

    prompt = f"""
You are an AI-powered DevOps CI/CD failure diagnosis assistant.

Your job is to explain a CI/CD failure and recommend the most
appropriate fix.

IMPORTANT:

The structured facts below were extracted programmatically from
the CI logs.

Treat these values as AUTHORITATIVE.

DO NOT reverse Expected and Actual.

DO NOT invent different values.

DO NOT say the GenAI job was skipped. It is running now.

DO NOT say Terraform or Docker failed if their status is SKIPPED.

Do not simply repeat the error.

Reason about the difference between the expected and actual value.

For an HTTP test failure:

Expected HTTP status = what the test expects.

Actual HTTP status = what the application actually returned.

If:

Expected = 200
Actual = 500

then the application returned an unexpected HTTP 500.

If the application file is identified as app/main.py and the
endpoint is /health, recommend investigating/fixing that endpoint.

Do not recommend changing a correct test expectation merely because
the test failed.

Use the actual evidence provided below.

STRUCTURED FACTS
================
{structured_facts}

PIPELINE CONTEXT
================
{context}

RAW TEST LOG
============
{test_logs}

TERRAFORM LOG
=============
{terraform_logs}


Return concise Markdown using EXACTLY these sections:

# AI Failure Diagnosis & Remediation

## Overall Assessment

State:

- Overall pipeline state
- Failed job
- Skipped jobs
- Whether GenAI analysis completed

## Failure Detection

Identify the failed test and endpoint.

Include:

Expected HTTP status: X
Actual HTTP status: Y

Use the structured facts exactly.

## Root Cause

Explain why the test failed.

For this failure, determine whether the application behavior
or the test expectation is more likely incorrect.

Do not reverse Expected and Actual.

## Evidence

List the concrete evidence:

- Test name
- Endpoint
- Expected status
- Actual status
- Relevant file

## Impact

Explain what the failure affects.

Do not claim that unrelated jobs failed.

## Recommended Fix

Give the smallest appropriate fix.

If the application is returning an unexpected HTTP 500 while
the test correctly expects HTTP 200, recommend fixing the
application endpoint in:

app/main.py

Do NOT recommend changing the test from 200 to 500.

## Verification Steps

Give concrete commands.

Use:

pytest app/ -v

and, where useful:

pytest app/test_main.py::test_health -v

## Preventive Recommendation

Give one or two recommendations directly related to this failure.

## AI Confidence

Choose exactly one:

High
Medium
Low

Give one short reason.
"""

    output = call_local_ai(prompt)

    Path("ai-log-summary.md").write_text(output)

    print("AI failure diagnosis generated successfully.")
    print()
    print(output)


if __name__ == "__main__":
    main()