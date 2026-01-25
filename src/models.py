"""Data models for the starred repos organizer."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Repository:
    """Represents a GitHub repository."""
    full_name: str
    name: str
    owner: str
    description: Optional[str] = None
    language: Optional[str] = None
    topics: list[str] = field(default_factory=list)
    stars: int = 0
    forks: int = 0
    url: str = ""
    homepage: Optional[str] = None
    starred_at: Optional[datetime] = None
    readme_excerpt: Optional[str] = None
    assigned_category: Optional[str] = None
    in_lists: list[str] = field(default_factory=list)
    
    @classmethod
    def from_api_response(cls, data: dict, starred_at: Optional[str] = None) -> "Repository":
        """Create a Repository from GitHub API response."""
        repo_data = data.get("repo", data)
        
        starred_dt = None
        if starred_at:
            try:
                starred_dt = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            full_name=repo_data["full_name"],
            name=repo_data["name"],
            owner=repo_data["owner"]["login"],
            description=repo_data.get("description"),
            language=repo_data.get("language"),
            topics=repo_data.get("topics", []),
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            url=repo_data["html_url"],
            homepage=repo_data.get("homepage"),
            starred_at=starred_dt,
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "full_name": self.full_name,
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "language": self.language,
            "topics": self.topics,
            "stars": self.stars,
            "forks": self.forks,
            "url": self.url,
            "homepage": self.homepage,
            "starred_at": self.starred_at.isoformat() if self.starred_at else None,
            "readme_excerpt": self.readme_excerpt,
            "assigned_category": self.assigned_category,
            "in_lists": self.in_lists,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Repository":
        """Create from dictionary."""
        starred_at = None
        if data.get("starred_at"):
            try:
                starred_at = datetime.fromisoformat(data["starred_at"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            full_name=data["full_name"],
            name=data["name"],
            owner=data.get("owner", data["full_name"].split("/")[0]),
            description=data.get("description"),
            language=data.get("language"),
            topics=data.get("topics", []),
            stars=data.get("stars", 0),
            forks=data.get("forks", 0),
            url=data.get("url", f"https://github.com/{data['full_name']}"),
            homepage=data.get("homepage"),
            starred_at=starred_at,
            readme_excerpt=data.get("readme_excerpt"),
            assigned_category=data.get("assigned_category"),
            in_lists=data.get("in_lists", []),
        )


@dataclass 
class Category:
    """Represents a category/list for organizing repos."""
    name: str
    description: str = ""
    emoji: str = ""
    repos: list[Repository] = field(default_factory=list)
    
    @property
    def count(self) -> int:
        return len(self.repos)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "emoji": self.emoji,
            "repos": [r.full_name for r in self.repos],
            "count": self.count,
        }


@dataclass
class CategorizedRepos:
    """Container for all categorized repositories."""
    categories: dict[str, Category] = field(default_factory=dict)
    uncategorized: list[Repository] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    llm_provider: str = ""
    llm_model: str = ""
    
    @property
    def total_repos(self) -> int:
        total = len(self.uncategorized)
        for cat in self.categories.values():
            total += cat.count
        return total
    
    @property
    def category_count(self) -> int:
        return len(self.categories)
    
    def add_repo(self, category_name: str, repo: Repository):
        """Add a repo to a category, creating it if needed."""
        if category_name not in self.categories:
            self.categories[category_name] = Category(name=category_name)
        self.categories[category_name].repos.append(repo)
        repo.assigned_category = category_name
    
    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "total_repos": self.total_repos,
            "category_count": self.category_count,
            "categories": {
                name: cat.to_dict() for name, cat in self.categories.items()
            },
            "uncategorized": [r.full_name for r in self.uncategorized],
        }
