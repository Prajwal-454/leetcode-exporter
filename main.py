#!/usr/bin/env python3
"""
LeetCode Exporter — main entry point.

Automatically downloads all accepted LeetCode solutions and
pushes them to a GitHub repository.

Usage:
    python main.py            # Full sync — download all solutions
    python main.py --sync     # Incremental sync — only new/updated solutions
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.panel import Panel

from api import LeetCodeAPI
from config import Config
from github import GitManager
from utils import (
    make_folder_name,
    get_file_extension,
    generate_problem_readme,
    generate_repo_readme,
    export_to_csv,
    compute_statistics,
    get_language_name,
)

console = Console()

# Metadata file used for incremental sync
METADATA_FILE = ".leetcode_meta.json"


class LeetCodeExporter:
    """
    Orchestrates the full export pipeline:
    fetch → download → save → generate READMEs → Git push.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize the exporter.

        Args:
            config: Application configuration.
        """
        self._config = config
        self._api = LeetCodeAPI(config)
        self._git = GitManager(
            repo_path=config.output_path,
            remote_url=config.github_repo or None,
            branch=config.github_branch,
        )
        self._output = config.output_path
        self._downloaded: list[dict[str, Any]] = []

    # ── Metadata persistence ─────────────────────────────────

    def _metadata_path(self) -> Path:
        """Return the path to the local metadata file."""
        return self._output / METADATA_FILE

    def _load_metadata(self) -> dict[str, Any]:
        """Load previously saved sync metadata."""
        path = self._metadata_path()
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_metadata(self, meta: dict[str, Any]) -> None:
        """Persist sync metadata to disk."""
        path = self._metadata_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    # ── Core pipeline ────────────────────────────────────────

    def run(self, incremental: bool = False) -> None:
        """
        Run the full export pipeline.

        Args:
            incremental: If True, only download new/updated solutions.
        """
        start_time = time.time()

        console.print(
            Panel(
                "[bold cyan]🚀 LeetCode Exporter[/bold cyan]\n"
                f"Mode: {'Incremental Sync' if incremental else 'Full Sync'}",
                border_style="cyan",
            )
        )

        # Step 1: Initialize Git
        self._git.initialize()

        # Step 2: Fetch solved problems
        problems = self._api.fetch_solved_problems()
        if not problems:
            console.print("[yellow]No solved problems found. Check your cookies.[/yellow]")
            return

        # Step 3: Load metadata for incremental sync
        metadata = self._load_metadata() if incremental else {}

        # Step 4: Download solutions
        self._download_solutions(problems, metadata, incremental)

        # Step 5: Generate repository README
        if self._downloaded:
            self._generate_repo_readme()

            # Step 6: Export CSV
            csv_path = export_to_csv(self._downloaded, self._output)
            console.log(f"[green]✓ Exported CSV: {csv_path}[/green]")

            # Step 7: Save metadata
            self._update_and_save_metadata(metadata)

            # Step 8: Print statistics
            self._print_statistics()

            # Step 9: Commit and push
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            self._git.commit_and_push(
                message=f"Update LeetCode solutions — {timestamp}"
            )
        else:
            console.print("[dim]No new solutions to download.[/dim]")

        elapsed = time.time() - start_time
        console.print(
            Panel(
                f"[bold green]✅ Done in {elapsed:.1f}s[/bold green]",
                border_style="green",
            )
        )

    def _download_solutions(
        self,
        problems: list[dict[str, Any]],
        metadata: dict[str, Any],
        incremental: bool,
    ) -> None:
        """
        Download solution code for each problem.

        Args:
            problems: List of solved problem dicts from the API.
            metadata: Previously saved sync metadata.
            incremental: Whether to skip already-synced problems.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading solutions...", total=len(problems))

            for problem in problems:
                qid = problem["questionId"]
                title = problem["title"]
                title_slug = problem["titleSlug"]
                difficulty = problem["difficulty"]
                tags = [t["name"] for t in problem.get("topicTags", [])]

                progress.update(task, description=f"[cyan]{qid}. {title}[/cyan]")

                # Check if we can skip this problem (incremental mode)
                if incremental and title_slug in metadata:
                    saved_ts = metadata[title_slug].get("timestamp", 0)
                    # We'll still check if there's a newer submission
                    sub = self._api.fetch_latest_accepted_submission(title_slug)
                    self._api.throttle()

                    if sub and sub["timestamp"] <= saved_ts:
                        self._downloaded.append({
                            "question_id": qid,
                            "title": title,
                            "title_slug": title_slug,
                            "difficulty": difficulty,
                            "tags": tags,
                            "language": metadata[title_slug].get("language", "Unknown"),
                            "timestamp": saved_ts,
                        })
                        progress.advance(task)
                        continue
                else:
                    sub = self._api.fetch_latest_accepted_submission(title_slug)
                    self._api.throttle()

                if sub is None:
                    console.log(f"[yellow]⚠ No accepted submission for {qid}. {title}[/yellow]")
                    progress.advance(task)
                    continue

                # Fetch code
                code = self._api.fetch_submission_code(sub["id"])
                self._api.throttle()

                if code is None:
                    console.log(f"[yellow]⚠ Could not fetch code for {qid}. {title}[/yellow]")
                    progress.advance(task)
                    continue

                # Save solution
                self._save_solution(
                    question_id=qid,
                    title=title,
                    title_slug=title_slug,
                    difficulty=difficulty,
                    tags=tags,
                    language=sub["lang"],
                    code=code,
                    timestamp=sub["timestamp"],
                )

                # Track downloaded problem
                self._downloaded.append({
                    "question_id": qid,
                    "title": title,
                    "title_slug": title_slug,
                    "difficulty": difficulty,
                    "tags": tags,
                    "language": sub["lang"],
                    "timestamp": sub["timestamp"],
                })

                console.log(f"[green]✓ Downloaded {qid} {title}[/green]")
                progress.advance(task)

    def _save_solution(
        self,
        question_id: str,
        title: str,
        title_slug: str,
        difficulty: str,
        tags: list[str],
        language: str,
        code: str,
        timestamp: int,
    ) -> None:
        """
        Save a solution and its README to disk.

        Args:
            question_id: Problem frontend ID.
            title: Problem title.
            title_slug: URL slug.
            difficulty: Easy/Medium/Hard.
            tags: Topic tags.
            language: Programming language slug.
            code: Solution source code.
            timestamp: Submission UNIX timestamp.
        """
        folder_name = make_folder_name(question_id, title)
        folder_path = self._output / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        # Write solution file
        ext = get_file_extension(language)
        solution_file = folder_path / f"{folder_name}{ext}"
        solution_file.write_text(code, encoding="utf-8")

        # Write problem README
        readme_content = generate_problem_readme(
            title=title,
            question_id=question_id,
            difficulty=difficulty,
            tags=tags,
            title_slug=title_slug,
            language=language,
            timestamp=timestamp,
        )
        readme_file = folder_path / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")

    def _generate_repo_readme(self) -> None:
        """Generate the top-level repository README."""
        readme_content = generate_repo_readme(self._downloaded)
        readme_path = self._output / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        console.log("[green]✓ Generated repository README.md[/green]")

    def _update_and_save_metadata(self, metadata: dict[str, Any]) -> None:
        """Update and persist the sync metadata."""
        for p in self._downloaded:
            metadata[p["title_slug"]] = {
                "question_id": p["question_id"],
                "title": p["title"],
                "timestamp": p["timestamp"],
                "language": p["language"],
            }
        self._save_metadata(metadata)

    def _print_statistics(self) -> None:
        """Print a summary table of statistics."""
        stats = compute_statistics(self._downloaded)

        # Difficulty table
        diff_table = Table(title="📊 Difficulty Breakdown", show_header=True)
        diff_table.add_column("Difficulty", style="bold")
        diff_table.add_column("Count", justify="right")
        for diff, count in stats["by_difficulty"].items():
            color = {"Easy": "green", "Medium": "yellow", "Hard": "red"}.get(diff, "white")
            diff_table.add_row(f"[{color}]{diff}[/{color}]", str(count))
        console.print(diff_table)

        # Language table
        lang_table = Table(title="🌐 Language Breakdown", show_header=True)
        lang_table.add_column("Language", style="bold")
        lang_table.add_column("Count", justify="right")
        for lang, count in sorted(
            stats["by_language"].items(), key=lambda x: x[1], reverse=True
        ):
            lang_table.add_row(lang, str(count))
        console.print(lang_table)


def main() -> None:
    """Parse CLI arguments and run the exporter."""
    parser = argparse.ArgumentParser(
        description="LeetCode Exporter — Download & push your solutions to GitHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py            Full sync — download all accepted solutions
  python main.py --sync     Incremental sync — only new/updated solutions
  python main.py --env .env.prod   Use a custom .env file
""",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Run an incremental sync (download only new/updated solutions).",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Path to a custom .env configuration file.",
    )

    args = parser.parse_args()

    try:
        config = Config.load(env_path=args.env)
    except ValueError as e:
        console.print(f"[red]Configuration error:\n{e}[/red]")
        sys.exit(1)

    exporter = LeetCodeExporter(config)
    exporter.run(incremental=args.sync)


if __name__ == "__main__":
    main()
