"""
Starred - AI-powered GitHub Stars Organizer

Automatically categorize your GitHub starred repositories using AI,
export to Markdown, and optionally sync with GitHub star lists.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .models import Repository, Category, CategorizedRepos
from .github import GitHubClient, GitHubListsClient
from .categorizer import Categorizer, quick_categorize
from .exporter import (
    MarkdownExporter,
    export_to_file,
    export_to_json,
    update_readme,
)
from .sync import ListSyncer

__all__ = [
    # Version
    "__version__",
    # Models
    "Repository",
    "Category",
    "CategorizedRepos",
    # GitHub
    "GitHubClient",
    "GitHubListsClient",
    # Categorization
    "Categorizer",
    "quick_categorize",
    # Export
    "MarkdownExporter",
    "export_to_file",
    "export_to_json",
    "update_readme",
    # Sync
    "ListSyncer",
]
