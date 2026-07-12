"""
Git integration module for LeetCode Exporter.

Handles Git repository initialization, staging, committing,
and pushing to a remote GitHub repository.
"""

from pathlib import Path
from typing import Optional

from git import Repo, InvalidGitRepositoryError, GitCommandNotFound
from rich.console import Console

console = Console()


class GitManager:
    """
    Manages Git operations for the solutions repository.

    Provides methods to initialize a repo, commit changes,
    and push to a remote with automatic conflict handling.
    """

    def __init__(
        self,
        repo_path: Path,
        remote_url: Optional[str] = None,
        branch: str = "main",
    ) -> None:
        """
        Initialize the GitManager.

        Args:
            repo_path: Path to the local repository directory.
            remote_url: URL of the remote GitHub repository.
            branch: Branch name to use (default: main).
        """
        self._repo_path = repo_path
        self._remote_url = remote_url
        self._branch = branch
        self._repo: Optional[Repo] = None

    def initialize(self) -> None:
        """
        Initialize or open the Git repository.

        Creates the repository directory and initializes Git if needed.
        Configures the remote origin if a remote URL is provided.
        """
        self._repo_path.mkdir(parents=True, exist_ok=True)

        try:
            self._repo = Repo(self._repo_path)
            console.log("[dim]Git repository already initialized.[/dim]")
        except InvalidGitRepositoryError:
            self._repo = Repo.init(self._repo_path)
            console.log("[green]✓ Initialized new Git repository.[/green]")

        # Configure remote if provided
        if self._remote_url:
            self._configure_remote()

    def _configure_remote(self) -> None:
        """Add or update the 'origin' remote."""
        if self._repo is None:
            return

        try:
            origin = self._repo.remote("origin")
            if origin.url != self._remote_url:
                origin.set_url(self._remote_url)
                console.log(f"[dim]Updated remote origin to {self._remote_url}[/dim]")
        except ValueError:
            self._repo.create_remote("origin", self._remote_url)
            console.log(f"[green]✓ Added remote origin: {self._remote_url}[/green]")

    def has_changes(self) -> bool:
        """
        Check if there are any uncommitted changes.

        Returns:
            True if there are staged, unstaged, or untracked changes.
        """
        if self._repo is None:
            return False

        return bool(
            self._repo.is_dirty(untracked_files=True)
            or self._repo.untracked_files
        )

    def commit_and_push(self, message: str = "Update LeetCode solutions") -> bool:
        """
        Stage all changes, commit, and push to the remote.

        Args:
            message: The commit message.

        Returns:
            True if changes were committed and pushed, False if
            there was nothing to commit.
        """
        if self._repo is None:
            console.log("[red]✗ Git repository not initialized.[/red]")
            return False

        if not self.has_changes():
            console.log("[dim]No changes to commit.[/dim]")
            if self._remote_url:
                self._push()
            return False

        try:
            # Stage all files
            self._repo.git.add(A=True)
            console.log("[dim]Staged all changes.[/dim]")

            # Commit
            self._repo.index.commit(message)
            console.log(f'[green]✓ Committed: "{message}"[/green]')

            # Ensure local branch name matches the expected remote branch
            current_branch = self._repo.active_branch.name
            if current_branch != self._branch:
                self._repo.git.branch("-M", self._branch)
                console.log(f"[dim]Renamed local branch '{current_branch}' to '{self._branch}'[/dim]")

            # Push if remote is configured
            if self._remote_url:
                self._push()

            return True

        except GitCommandNotFound:
            console.log(
                "[red]✗ Git is not installed. Please install Git and try again.[/red]"
            )
            return False
        except Exception as e:
            console.log(f"[red]✗ Git error: {e}[/red]")
            return False

    def _push(self) -> None:
        """Push commits to the remote repository."""
        if self._repo is None:
            return

        try:
            origin = self._repo.remote("origin")

            # Check if remote branch exists
            try:
                origin.pull(self._branch, rebase=True)
            except Exception:
                # Remote branch might not exist yet; that's okay
                pass

            origin.push(self._branch, set_upstream=True)
            console.log(
                f"[green]✓ Pushed to {self._remote_url} ({self._branch})[/green]"
            )
        except Exception as e:
            console.log(
                f"[yellow]⚠ Push failed: {e}. You may need to push manually.[/yellow]"
            )
