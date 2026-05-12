#!/usr/bin/env python3
"""
Collect work information from git repository for a specific date.
"""

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


def run_git_command(cmd: List[str], cwd: str = None) -> str:
    """Run a git command and return the output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return ""


def get_git_commits(date: str, cwd: str = None) -> List[Dict[str, Any]]:
    """Get all commits for a specific date."""
    # Git log format: hash|author|date|subject
    log_format = "%H|%an|%ad|%s"
    
    # Get commits for the date (from 00:00 to 23:59)
    cmd = [
        "git", "log",
        f"--since={date} 00:00:00",
        f"--until={date} 23:59:59",
        f"--format={log_format}",
        "--date=iso"
    ]
    
    output = run_git_command(cmd, cwd)
    commits = []
    
    if output:
        for line in output.split('\n'):
            if line.strip():
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
    
    return commits


def get_file_changes(date: str, cwd: str = None) -> Dict[str, Any]:
    """Get file changes for a specific date."""
    # Get list of changed files
    cmd = [
        "git", "log",
        f"--since={date} 00:00:00",
        f"--until={date} 23:59:59",
        "--name-status",
        "--format="
    ]
    
    output = run_git_command(cmd, cwd)
    
    added = []
    modified = []
    deleted = []
    
    if output:
        for line in output.split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    filepath = parts[1]
                    
                    if status == 'A':
                        added.append(filepath)
                    elif status == 'M':
                        modified.append(filepath)
                    elif status == 'D':
                        deleted.append(filepath)
                    elif status.startswith('R'):
                        # Renamed files
                        old_path = parts[1]
                        new_path = parts[2] if len(parts) > 2 else ""
                        modified.append(f"{old_path} -> {new_path}")
    
    return {
        "added": list(set(added)),
        "modified": list(set(modified)),
        "deleted": list(set(deleted))
    }


def get_code_statistics(date: str, cwd: str = None) -> Dict[str, int]:
    """Get code statistics (lines added/removed) for a specific date."""
    cmd = [
        "git", "log",
        f"--since={date} 00:00:00",
        f"--until={date} 23:59:59",
        "--numstat",
        "--format="
    ]
    
    output = run_git_command(cmd, cwd)
    
    added = 0
    removed = 0
    files_changed = set()
    
    if output:
        for line in output.split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        lines_added = int(parts[0]) if parts[0] != '-' else 0
                        lines_removed = int(parts[1]) if parts[1] != '-' else 0
                        filepath = parts[2]
                        
                        added += lines_added
                        removed += lines_removed
                        files_changed.add(filepath)
                    except ValueError:
                        continue
    
    return {
        "lines_added": added,
        "lines_removed": removed,
        "files_changed": len(files_changed)
    }


def collect_work_info(date: str, output_path: str = None) -> Dict[str, Any]:
    """Collect all work information for a specific date."""
    
    # Check if we're in a git repository
    try:
        run_git_command(["git", "rev-parse", "--git-dir"])
    except:
        print("Error: Not in a git repository")
        return {}
    
    print(f"📊 Collecting work information for {date}...")
    
    # Collect all information
    work_info = {
        "date": date,
        "repository": os.path.basename(os.getcwd()),
        "git_commits": get_git_commits(date),
        "file_changes": get_file_changes(date),
        "statistics": get_code_statistics(date)
    }
    
    # Print summary
    print(f"\n✅ Collection complete!")
    print(f"  Commits: {len(work_info['git_commits'])}")
    print(f"  Files added: {len(work_info['file_changes']['added'])}")
    print(f"  Files modified: {len(work_info['file_changes']['modified'])}")
    print(f"  Files deleted: {len(work_info['file_changes']['deleted'])}")
    print(f"  Lines added: {work_info['statistics']['lines_added']}")
    print(f"  Lines removed: {work_info['statistics']['lines_removed']}")
    
    # Save to file if output path specified
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(work_info, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Work information saved to: {output_file}")
    
    return work_info


def main():
    parser = argparse.ArgumentParser(
        description="Collect work information from git repository for a specific date"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date in YYYY-MM-DD format (default: today)",
        default=datetime.now().strftime("%Y-%m-%d")
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path",
        default=None
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
        return
    
    collect_work_info(args.date, args.output)


if __name__ == "__main__":
    main()
