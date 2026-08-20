from pathlib import Path


def read_file(path):
    file = Path(path)

    if file.exists():
        return file.read_text(errors="ignore")

    return f"{path} was not found."


def analyze_log(name, content):
    lower = content.lower()

    if "error" in lower or "failed" in lower or "failure" in lower:
        status = "Issues detected"
    else:
        status = "No obvious errors detected"

    return f"""### {name}

**Analysis:** {status}

Log size: {len(content)} characters.
"""


def main():
    log_files = [
        "workflow-logs.txt",
        "terraform-plan-logs.txt",
    ]

    summary_parts = []

    for log_file in log_files:
        content = read_file(log_file)
        summary_parts.append(
            analyze_log(log_file, content)
        )

    context = read_file("poc-context.txt")

    output = f"""# AI Pipeline Log Summary

## Pipeline Context

```text
{context}