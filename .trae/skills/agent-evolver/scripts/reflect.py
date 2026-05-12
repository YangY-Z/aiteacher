#!/usr/bin/env python3
"""
Reflection data collector for agent-evolver.

Analyzes git history since the last reflection entry and produces a structured
summary of recent changes that can be used as input for the meta-cognitive
reflection protocol.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


EVOLUTION_DIR = Path.home() / ".claude" / "evolution"
RAW_DIR = EVOLUTION_DIR / "raw"


def run_git(project_root: str, *args: str) -> str:
    """Run a git command in the project root."""
    result = subprocess.run(
        ["git"] + list(args),
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_last_reflection_date(project_root: str) -> str | None:
    """Find the date of the most recent reflection entry for this project."""
    project_name = Path(project_root).name
    project_raw_dir = RAW_DIR / project_name

    if not project_raw_dir.exists():
        return None

    # Find the most recent raw entry file
    files = sorted(project_raw_dir.glob("*.md"), reverse=True)
    if not files:
        return None

    # Extract date from filename (YYYY-MM-DD.md)
    stem = files[0].stem  # e.g., "2026-04-28"
    return stem


def get_default_since_date() -> str:
    """Default to 7 days ago if no previous reflection found."""
    seven_days_ago = datetime.now() - timedelta(days=7)
    return seven_days_ago.strftime("%Y-%m-%d")


def collect_git_info(project_root: str, since_date: str) -> dict:
    """Collect git commit and diff information since the given date."""
    info = {
        "since_date": since_date,
        "project_root": project_root,
        "project_name": Path(project_root).name,
        "collection_time": datetime.now().isoformat(),
    }

    # Get commits
    log_format = "%h|%s|%an|%ad"
    log = run_git(
        project_root,
        "log",
        f"--since={since_date}",
        "--pretty=format:" + log_format,
        "--date=short",
    )

    commits = []
    if log:
        for line in log.split("\n"):
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })

    info["commits"] = commits
    info["commit_count"] = len(commits)

    # Get changed files with stats
    diff_stat = run_git(
        project_root,
        "diff",
        f"--since={since_date}",
        "--stat",
    )

    changed_files = []
    if diff_stat:
        for line in diff_stat.split("\n"):
            line = line.strip()
            if not line or "files changed" in line:
                continue
            # Format: "  path/to/file | 10 +++---"
            parts = line.split("|")
            if len(parts) == 2:
                file_path = parts[0].strip()
                changed_files.append({"path": file_path})

    info["changed_files"] = changed_files
    info["file_count"] = len(changed_files)

    # Get diff content (truncated to avoid excessive output)
    diff_content = run_git(
        project_root,
        "diff",
        f"--since={since_date}",
        "--stat",
        "--diff-filter=M",  # Only modified files for details
    )

    info["diff_summary"] = diff_stat

    # Check for worklog entries
    worklog_dir = Path(project_root) / "worklog"
    worklog_entries = []
    if worklog_dir.exists():
        for d in sorted(worklog_dir.glob("20*"), reverse=True):
            if d.name >= since_date:
                worklog_entries.append(d.name)

    info["worklog_entries"] = worklog_entries

    return info


def format_report(info: dict) -> str:
    """Format the collected information as a readable report."""
    lines = []
    lines.append(f"# Reflection Data Collection")
    lines.append(f"")
    lines.append(f"**Project:** {info['project_name']}")
    lines.append(f"**Since:** {info['since_date']}")
    lines.append(f"**Collected at:** {info['collection_time']}")
    lines.append(f"")

    # Commits
    lines.append(f"## Commits ({info['commit_count']})")
    if info["commits"]:
        for c in info["commits"]:
            lines.append(f"- `{c['hash']}` {c['date']} | {c['message']} ({c['author']})")
    else:
        lines.append("(No commits found)")
    lines.append("")

    # Changed files
    lines.append(f"## Changed Files ({info['file_count']})")
    if info["changed_files"]:
        for f in info["changed_files"]:
            lines.append(f"- `{f['path']}`")
    else:
        lines.append("(No file changes found)")
    lines.append("")

    # Worklog entries
    if info["worklog_entries"]:
        lines.append(f"## Worklog Entries")
        for entry in info["worklog_entries"]:
            lines.append(f"- `worklog/{entry}/`")
        lines.append("")

    # Summary stats
    lines.append(f"## Summary")
    lines.append(f"- Commits: {info['commit_count']}")
    lines.append(f"- Files changed: {info['file_count']}")
    lines.append(f"- Worklog days: {len(info['worklog_entries'])}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Collect reflection data from git history")
    parser.add_argument("--project-root", required=True, help="Path to the project root")
    parser.add_argument("--since", default=None, help="Start date (YYYY-MM-DD), defaults to last reflection or 7 days ago")
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)

    if not os.path.isdir(os.path.join(project_root, ".git")):
        print(f"Error: {project_root} is not a git repository", file=sys.stderr)
        sys.exit(1)

    since_date = args.since
    if not since_date:
        since_date = get_last_reflection_date(project_root) or get_default_since_date()

    info = collect_git_info(project_root, since_date)
    report = format_report(info)
    print(report)


if __name__ == "__main__":
    main()
