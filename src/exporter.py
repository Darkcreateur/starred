"""Export categorized repos to Markdown and update README files."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CategorizedRepos, Repository, Category

logger = logging.getLogger(__name__)


# Placeholder tags for README integration
START_TAG = "<!-- STARRED_REPOS_START -->"
END_TAG = "<!-- STARRED_REPOS_END -->"


class MarkdownExporter:
    """Export categorized repositories to Markdown format."""
    
    def __init__(
        self,
        show_stars: bool = True,
        show_language: bool = True,
        show_description: bool = True,
        max_description_length: int = 100,
        sort_by: str = "stars",  # stars, name, starred_at
        repos_per_category: Optional[int] = None,
        compact_mode: bool = False,
    ):
        """
        Initialize the exporter.
        
        Args:
            show_stars: Show star count
            show_language: Show programming language
            show_description: Show repo description
            max_description_length: Truncate descriptions
            sort_by: How to sort repos within categories
            repos_per_category: Limit repos per category (None for all)
            compact_mode: Use compact single-line format
        """
        self.show_stars = show_stars
        self.show_language = show_language
        self.show_description = show_description
        self.max_description_length = max_description_length
        self.sort_by = sort_by
        self.repos_per_category = repos_per_category
        self.compact_mode = compact_mode
    
    def _sort_repos(self, repos: list[Repository]) -> list[Repository]:
        """Sort repositories based on configured sort order."""
        if self.sort_by == "stars":
            return sorted(repos, key=lambda r: r.stars, reverse=True)
        elif self.sort_by == "name":
            return sorted(repos, key=lambda r: r.full_name.lower())
        elif self.sort_by == "starred_at":
            return sorted(
                repos,
                key=lambda r: r.starred_at or datetime.min,
                reverse=True
            )
        return repos
    
    def _format_repo(self, repo: Repository) -> str:
        """Format a single repository entry."""
        parts = [f"[{repo.full_name}]({repo.url})"]
        
        if self.show_language and repo.language:
            parts.append(f"`{repo.language}`")
        
        if self.show_stars:
            parts.append(f"⭐ {repo.stars:,}")
        
        if self.show_description and repo.description:
            desc = repo.description[:self.max_description_length]
            if len(repo.description) > self.max_description_length:
                desc += "..."
            parts.append(f"- {desc}")
        
        if self.compact_mode:
            return " ".join(parts)
        else:
            return f"- {' '.join(parts)}"
    
    def _format_category(self, category: Category) -> list[str]:
        """Format a category and its repos."""
        lines = []
        
        # Category header
        lines.append(f"## {category.name}")
        if category.description:
            lines.append(f"*{category.description}*")
        lines.append("")
        
        # Sort and limit repos
        repos = self._sort_repos(category.repos)
        if self.repos_per_category:
            repos = repos[:self.repos_per_category]
        
        # Format repos
        for repo in repos:
            lines.append(self._format_repo(repo))
        
        # Show truncation notice
        if self.repos_per_category and len(category.repos) > self.repos_per_category:
            remaining = len(category.repos) - self.repos_per_category
            lines.append(f"- *...and {remaining} more*")
        
        lines.append("")
        return lines
    
    def generate(
        self,
        categorized: CategorizedRepos,
        title: str = "⭐ My Starred Repositories",
        include_toc: bool = True,
        include_stats: bool = True,
        include_timestamp: bool = True,
    ) -> str:
        """
        Generate full Markdown document.
        
        Args:
            categorized: Categorized repositories
            title: Document title
            include_toc: Include table of contents
            include_stats: Include statistics section
            include_timestamp: Include generation timestamp
        
        Returns:
            Markdown string
        """
        lines = [f"# {title}", ""]
        
        # Generation info
        if include_timestamp:
            lines.append(f"*Last updated: {categorized.generated_at.strftime('%Y-%m-%d %H:%M UTC')}*")
            lines.append(f"*Categorized using {categorized.llm_provider} ({categorized.llm_model})*")
            lines.append("")
        
        # Statistics
        if include_stats:
            lines.append(f"**{categorized.total_repos:,}** repositories organized into **{categorized.category_count}** categories")
            lines.append("")
        
        # Table of contents
        if include_toc:
            lines.append("## 📑 Table of Contents")
            lines.append("")
            
            # Sort categories by count
            sorted_cats = sorted(
                categorized.categories.values(),
                key=lambda c: c.count,
                reverse=True
            )
            
            for cat in sorted_cats:
                if cat.count > 0:
                    # Create anchor from category name
                    anchor = cat.name.lower()
                    anchor = re.sub(r'[^\w\s-]', '', anchor)
                    anchor = re.sub(r'\s+', '-', anchor.strip())
                    lines.append(f"- [{cat.name}](#{anchor}) ({cat.count})")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Categories
        sorted_cats = sorted(
            categorized.categories.values(),
            key=lambda c: c.count,
            reverse=True
        )
        
        for category in sorted_cats:
            if category.count > 0:
                lines.extend(self._format_category(category))
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by [Starred](https://github.com/yourusername/starred) - AI-powered GitHub stars organizer*")
        
        return "\n".join(lines)
    
    def generate_for_readme(
        self,
        categorized: CategorizedRepos,
        max_repos: int = 50,
        max_categories: int = 10,
    ) -> str:
        """
        Generate a compact version suitable for embedding in README.
        
        Args:
            categorized: Categorized repositories
            max_repos: Maximum total repos to show
            max_categories: Maximum categories to show
        
        Returns:
            Markdown string (without header)
        """
        lines = []
        
        # Sort categories by count and limit
        sorted_cats = sorted(
            categorized.categories.values(),
            key=lambda c: c.count,
            reverse=True
        )[:max_categories]
        
        repos_shown = 0
        repos_per_cat = max(max_repos // len(sorted_cats), 3) if sorted_cats else 5
        
        for category in sorted_cats:
            if category.count == 0:
                continue
            
            lines.append(f"### {category.name}")
            lines.append("")
            
            repos = self._sort_repos(category.repos)[:repos_per_cat]
            
            for repo in repos:
                if repos_shown >= max_repos:
                    break
                lines.append(self._format_repo(repo))
                repos_shown += 1
            
            lines.append("")
            
            if repos_shown >= max_repos:
                break
        
        lines.append(f"*[View all {categorized.total_repos} starred repositories →](STARRED_REPOS.md)*")
        
        return "\n".join(lines)


def export_to_file(
    categorized: CategorizedRepos,
    output_path: str | Path,
    **kwargs,
) -> Path:
    """
    Export categorized repos to a Markdown file.
    
    Args:
        categorized: Categorized repositories
        output_path: Output file path
        **kwargs: Arguments passed to MarkdownExporter.generate()
    
    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    exporter = MarkdownExporter()
    
    content = exporter.generate(categorized, **kwargs)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    
    logger.info(f"Exported to {output_path}")
    return output_path


def export_to_json(
    categorized: CategorizedRepos,
    output_path: str | Path,
) -> Path:
    """
    Export categorized repos to JSON.
    
    Args:
        categorized: Categorized repositories
        output_path: Output file path
    
    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    
    data = categorized.to_dict()
    
    # Also include full repo data
    data["repositories"] = {}
    for cat in categorized.categories.values():
        for repo in cat.repos:
            data["repositories"][repo.full_name] = repo.to_dict()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    
    logger.info(f"Exported JSON to {output_path}")
    return output_path


def update_readme(
    readme_path: str | Path,
    categorized: CategorizedRepos,
    max_repos: int = 50,
    max_categories: int = 10,
    create_if_missing: bool = False,
) -> bool:
    """
    Update a README file with starred repos content between placeholder tags.
    
    The README should contain these tags:
    <!-- STARRED_REPOS_START -->
    (content will be replaced here)
    <!-- STARRED_REPOS_END -->
    
    Args:
        readme_path: Path to README file
        categorized: Categorized repositories
        max_repos: Maximum repos to show
        max_categories: Maximum categories to show
        create_if_missing: Create README with placeholders if missing
    
    Returns:
        True if updated successfully
    """
    readme_path = Path(readme_path)
    
    # Generate content
    exporter = MarkdownExporter(compact_mode=True)
    content = exporter.generate_for_readme(
        categorized,
        max_repos=max_repos,
        max_categories=max_categories,
    )
    
    # Read existing README or create template
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8")
    elif create_if_missing:
        readme_content = f"""# My Profile

{START_TAG}
<!-- Starred repos will be inserted here -->
{END_TAG}
"""
        logger.info(f"Creating new README at {readme_path}")
    else:
        logger.error(f"README not found: {readme_path}")
        return False
    
    # Check for placeholder tags
    if START_TAG not in readme_content or END_TAG not in readme_content:
        logger.error(
            f"README does not contain placeholder tags. "
            f"Add these tags where you want starred repos:\n"
            f"{START_TAG}\n{END_TAG}"
        )
        return False
    
    # Replace content between tags
    pattern = f"{re.escape(START_TAG)}.*?{re.escape(END_TAG)}"
    replacement = f"{START_TAG}\n\n{content}\n\n{END_TAG}"
    
    new_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
    
    # Write updated README
    readme_path.write_text(new_content, encoding="utf-8")
    logger.info(f"Updated README at {readme_path}")
    
    return True


def create_placeholder_readme(output_path: str | Path) -> Path:
    """
    Create a template README with placeholder tags.
    
    Args:
        output_path: Path for the new README
    
    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    
    template = f"""# Hi there! 👋

Welcome to my GitHub profile!

## ⭐ My Starred Repositories

{START_TAG}
<!-- This section is auto-updated by Starred -->
<!-- See: https://github.com/yourusername/starred -->

*Run the starred action to populate this section.*
{END_TAG}

## 📫 How to reach me

- Twitter: [@yourhandle](https://twitter.com/yourhandle)
- LinkedIn: [Your Name](https://linkedin.com/in/yourprofile)

---

*Profile README updated by [Starred](https://github.com/yourusername/starred)*
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template, encoding="utf-8")
    
    logger.info(f"Created template README at {output_path}")
    return output_path
