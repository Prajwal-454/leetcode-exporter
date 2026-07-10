"""
Configuration module for LeetCode Exporter.

Reads configuration from environment variables and .env file.
Provides centralized access to all configuration values.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


# LeetCode API endpoints
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_BASE_URL = "https://leetcode.com"

# Language extension mapping
LANGUAGE_EXTENSIONS: dict[str, str] = {
    "python": ".py",
    "python3": ".py",
    "java": ".java",
    "cpp": ".cpp",
    "c": ".c",
    "csharp": ".cs",
    "javascript": ".js",
    "typescript": ".ts",
    "go": ".go",
    "ruby": ".rb",
    "swift": ".swift",
    "kotlin": ".kt",
    "rust": ".rs",
    "scala": ".scala",
    "php": ".php",
    "dart": ".dart",
    "racket": ".rkt",
    "erlang": ".erl",
    "elixir": ".ex",
    "mysql": ".sql",
    "mssql": ".sql",
    "oraclesql": ".sql",
    "postgresql": ".sql",
    "bash": ".sh",
}

# Language display names
LANGUAGE_NAMES: dict[str, str] = {
    "python": "Python",
    "python3": "Python 3",
    "java": "Java",
    "cpp": "C++",
    "c": "C",
    "csharp": "C#",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "go": "Go",
    "ruby": "Ruby",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "rust": "Rust",
    "scala": "Scala",
    "php": "PHP",
    "dart": "Dart",
    "racket": "Racket",
    "erlang": "Erlang",
    "elixir": "Elixir",
    "mysql": "MySQL",
    "mssql": "MS SQL",
    "oraclesql": "Oracle SQL",
    "postgresql": "PostgreSQL",
    "bash": "Bash",
}


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    leetcode_session: str = ""
    csrf_token: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    output_folder: str = "LeetCode"

    @classmethod
    def load(cls, env_path: Optional[str] = None) -> "Config":
        """
        Load configuration from .env file and environment variables.

        Args:
            env_path: Optional path to .env file. Defaults to .env in CWD.

        Returns:
            A populated Config instance.

        Raises:
            ValueError: If required configuration values are missing.
        """
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        config = cls(
            leetcode_session=os.getenv("LEETCODE_SESSION", ""),
            csrf_token=os.getenv("CSRFTOKEN", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
            github_branch=os.getenv("GITHUB_BRANCH", "main"),
            output_folder=os.getenv("OUTPUT_FOLDER", "LeetCode"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate that all required configuration values are present."""
        errors: list[str] = []
        if not self.leetcode_session:
            errors.append("LEETCODE_SESSION is required.")
        if not self.csrf_token:
            errors.append("CSRFTOKEN is required.")
        if errors:
            raise ValueError(
                "Missing required configuration:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    @property
    def output_path(self) -> Path:
        """Return the output folder as a Path object."""
        return Path(self.output_folder)

    @property
    def cookies(self) -> dict[str, str]:
        """Return LeetCode session cookies as a dictionary."""
        return {
            "LEETCODE_SESSION": self.leetcode_session,
            "csrftoken": self.csrf_token,
        }

    @property
    def headers(self) -> dict[str, str]:
        """Return HTTP headers required for LeetCode API requests."""
        return {
            "Content-Type": "application/json",
            "Referer": LEETCODE_BASE_URL,
            "x-csrftoken": self.csrf_token,
            "Origin": LEETCODE_BASE_URL,
        }
