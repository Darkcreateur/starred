"""AI-powered repository categorization engine."""

import json
import logging
from typing import Optional

from .models import Repository, Category, CategorizedRepos
from .llm import BaseLLMProvider

logger = logging.getLogger(__name__)


DEFAULT_CATEGORIES = [
    ("🤖 AI & Machine Learning", "Machine learning, deep learning, NLP, computer vision, AI tools"),
    ("🌐 Web Development", "Frontend, backend, fullstack frameworks and tools"),
    ("⚙️ DevOps & Infrastructure", "CI/CD, containers, orchestration, cloud infrastructure"),
    ("🔧 CLI Tools", "Command line utilities and terminal tools"),
    ("🔒 Security & Privacy", "Security tools, encryption, privacy-focused software"),
    ("📊 Data Engineering", "Data pipelines, ETL, databases, analytics"),
    ("📱 Mobile Development", "iOS, Android, cross-platform mobile frameworks"),
    ("🖥️ Desktop Applications", "Desktop apps, GUI frameworks, system utilities"),
    ("📚 Documentation & Learning", "Learning resources, tutorials, documentation tools"),
    ("🔌 APIs & SDKs", "API clients, SDKs, integrations"),
    ("🧪 Testing & QA", "Testing frameworks, quality assurance tools"),
    ("🎨 Design & UI", "Design tools, UI components, styling"),
    ("💾 Databases", "Database systems, ORMs, data storage"),
    ("🏠 Self-Hosted", "Self-hosted alternatives, privacy-focused services"),
    ("🚀 Starter Templates", "Boilerplates, starter kits, project templates"),
    ("📦 Miscellaneous", "Other useful repositories"),
]


class Categorizer:
    """AI-powered repository categorizer using LLM providers."""
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        categories: Optional[list[tuple[str, str]]] = None,
    ):
        """
        Initialize the categorizer.
        
        Args:
            llm: LLM provider instance
            categories: List of (name, description) tuples for categories.
                       If None, will use defaults or generate dynamically.
        """
        self.llm = llm
        self.categories = categories or DEFAULT_CATEGORIES
    
    def generate_categories(
        self,
        repos: list[Repository],
        preferences: str = "",
        max_categories: int = 20,
    ) -> list[tuple[str, str]]:
        """
        Generate optimal categories based on the repositories and user preferences.
        
        Args:
            repos: List of repositories to analyze
            preferences: User preferences for categorization
            max_categories: Maximum number of categories to generate
        
        Returns:
            List of (name, description) tuples
        """
        # Sample repos for analysis (to fit in context)
        sample_size = min(150, len(repos))
        sample_repos = repos[:sample_size]
        
        repos_summary = "\n".join([
            f"- {r.full_name}: {(r.description or 'No description')[:100]} "
            f"[{r.language or 'unknown'}] topics: {', '.join(r.topics[:5])}"
            for r in sample_repos
        ])
        
        prompt = f"""Analyze these GitHub repositories and create {max_categories} optimal categories for organizing them.

REPOSITORIES ({len(sample_repos)} of {len(repos)} total):
{repos_summary}

USER PREFERENCES:
{preferences or "Create general developer-focused categories suitable for organizing a diverse set of repositories."}

REQUIREMENTS:
1. Each category should have an emoji prefix (single emoji)
2. Category names should be concise (2-4 words after emoji)
3. Categories should be mutually exclusive where possible
4. Include descriptions to help with classification
5. Always include a "📦 Miscellaneous" category for edge cases
6. Make categories practical and useful for a developer

Return ONLY valid JSON in this exact format:
[
  {{"name": "🤖 AI & Machine Learning", "description": "Machine learning, deep learning, NLP, AI tools"}},
  {{"name": "🌐 Web Development", "description": "Frontend, backend, fullstack frameworks"}}
]"""

        try:
            result = self.llm.complete_json(prompt)
            categories = [
                (cat["name"], cat.get("description", ""))
                for cat in result
            ]
            logger.info(f"Generated {len(categories)} categories")
            return categories
        except Exception as e:
            logger.warning(f"Failed to generate categories: {e}. Using defaults.")
            return DEFAULT_CATEGORIES
    
    def categorize_batch(
        self,
        repos: list[Repository],
        categories: list[tuple[str, str]],
    ) -> dict[str, str]:
        """
        Categorize a batch of repositories.
        
        Args:
            repos: Repositories to categorize
            categories: Available categories as (name, description) tuples
        
        Returns:
            Dict mapping repo full_name to category name
        """
        # Build category list for prompt
        cat_list = "\n".join([
            f'- "{name}": {desc}' for name, desc in categories
        ])
        
        # Build repo list for prompt
        repos_list = []
        for r in repos:
            info = {
                "full_name": r.full_name,
                "description": (r.description or "")[:200],
                "language": r.language or "unknown",
                "topics": r.topics[:8],
            }
            if r.readme_excerpt:
                info["readme_preview"] = r.readme_excerpt[:300]
            repos_list.append(info)
        
        prompt = f"""Categorize each GitHub repository into exactly ONE of these categories:

CATEGORIES:
{cat_list}

REPOSITORIES TO CATEGORIZE:
{json.dumps(repos_list, indent=2)}

RULES:
1. Each repository must be assigned to exactly one category
2. Choose the most specific applicable category
3. Use "📦 Miscellaneous" only when no other category fits
4. Base decisions on: description, language, topics, and README preview

Return ONLY valid JSON mapping full_name to category name:
{{"owner/repo1": "🤖 AI & Machine Learning", "owner/repo2": "🌐 Web Development"}}"""

        try:
            return self.llm.complete_json(prompt)
        except Exception as e:
            logger.error(f"Categorization failed: {e}")
            # Return all as miscellaneous on failure
            misc = next((name for name, _ in categories if "misc" in name.lower()), categories[-1][0])
            return {r.full_name: misc for r in repos}
    
    def categorize_all(
        self,
        repos: list[Repository],
        categories: Optional[list[tuple[str, str]]] = None,
        batch_size: int = 25,
        preferences: str = "",
    ) -> CategorizedRepos:
        """
        Categorize all repositories.
        
        Args:
            repos: All repositories to categorize
            categories: Categories to use (None to auto-generate)
            batch_size: Number of repos per LLM call
            preferences: User preferences for category generation
        
        Returns:
            CategorizedRepos object with all categorizations
        """
        # Generate or use provided categories
        if categories is None:
            if preferences:
                categories = self.generate_categories(repos, preferences)
            else:
                categories = self.categories
        
        result = CategorizedRepos(
            llm_provider=self.llm.name,
            llm_model=self.llm.model,
        )
        
        # Initialize categories
        for name, desc in categories:
            result.categories[name] = Category(name=name, description=desc)
        
        # Process in batches
        total_batches = (len(repos) + batch_size - 1) // batch_size
        
        for i in range(0, len(repos), batch_size):
            batch = repos[i:i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} repos)...")
            
            assignments = self.categorize_batch(batch, categories)
            
            for repo in batch:
                category = assignments.get(repo.full_name)
                
                # Validate category exists
                if category and category in result.categories:
                    result.add_repo(category, repo)
                else:
                    # Find miscellaneous or first category
                    fallback = next(
                        (name for name in result.categories if "misc" in name.lower()),
                        list(result.categories.keys())[0]
                    )
                    result.add_repo(fallback, repo)
        
        # Log summary
        logger.info(f"Categorization complete: {result.total_repos} repos in {result.category_count} categories")
        for name, cat in sorted(result.categories.items(), key=lambda x: -x[1].count):
            if cat.count > 0:
                logger.info(f"  {name}: {cat.count} repos")
        
        return result


def quick_categorize(
    repos: list[Repository],
    llm: BaseLLMProvider,
    preferences: str = "",
) -> CategorizedRepos:
    """
    Quick helper to categorize repos with default settings.
    
    Args:
        repos: Repositories to categorize
        llm: LLM provider
        preferences: Optional user preferences
    
    Returns:
        CategorizedRepos object
    """
    categorizer = Categorizer(llm)
    return categorizer.categorize_all(repos, preferences=preferences)
