from pathlib import Path


def read_file(path):
    file_path = Path(path)

    if file_path.exists():
        return file_path.read_text(errors="ignore")

    return f"{path} was not found."


def analyze_log(name, content):
    lower = content.lower()

    if "error" in lower or "failed" in lower or "failure" in lower:
        status = "Issues detected"
    else:
        status = "No obvious errors detected"

    return (
        f"### {name}\n\n"
        f"**Analysis:** {status}\n\n"
        f"Log size: {len(content)} characters.\n"
    )


def main():
    log_files = [
        "workflow-logs.txt",
        "terraform-plan.log",
    ]

    summary_parts = []

    for log_file in log_files:
        content = read_file(log_file)
        summary_parts.append(
            analyze_log(log_file, content)
        )

    context = read_file("poc-context.txt")

    output = (
        "# AI Pipeline Log Summary\n\n"
        "## Pipeline Context\n\n"
        "```text\n"
        f"{context}\n"
        "```\n\n"
        "## Automated Log Analysis\n\n"
        f"{chr(10).join(summary_parts)}\n"
        "## Overall Analysis\n\n"
        "The GitHub Actions pipeline logs were collected and "
        "analyzed automatically.\n\n"
        "The analysis stage demonstrates how pipeline execution "
        "data can be transformed into a human-readable summary "
        "as part of the CI/CD workflow.\n\n"
        "## Next Steps\n\n"
        "Review any stages marked as having issues and inspect "
        "the corresponding GitHub Actions logs for detailed "
        "troubleshooting.\n"
    )

    Path("ai-log-summary.md").write_text(output)

    print("AI log summary generated successfully.")


if __name__ == "__main__":
    main()