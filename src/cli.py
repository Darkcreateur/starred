#!/usr/bin/env python3
"""
Starred - AI-powered GitHub Stars Organizer

Automatically categorize your GitHub starred repositories using AI,
export to Markdown, and optionally sync with GitHub star lists.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def cmd_fetch(args):
    """Fetch starred repositories from GitHub."""
    from .github import GitHubClient
    from .models import Repository
    
    if not args.token:
        logger.error("GitHub token required. Set GH_TOKEN or use --token")
        return 1
    
    client = GitHubClient(args.token, args.username)
    
    logger.info(f"Fetching starred repos for {client.username}...")
    repos = client.get_starred_repos(
        per_page=100,
        max_repos=args.max_repos,
    )
    
    # Fetch READMEs if requested
    if args.with_readme:
        logger.info("Fetching README excerpts (this may take a while)...")
        for i, repo in enumerate(repos):
            if i % 20 == 0:
                logger.info(f"  Progress: {i}/{len(repos)}")
            repo.readme_excerpt = client.get_readme(repo.full_name)
    
    # Save to cache
    cache_path = Path(args.output or f"data/{client.username}_starred.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(cache_path, "w") as f:
        json.dump([r.to_dict() for r in repos], f, indent=2, default=str)
    
    logger.info(f"Saved {len(repos)} repos to {cache_path}")
    return 0


def cmd_categorize(args):
    """Categorize repositories using AI."""
    from .models import Repository
    from .categorizer import Categorizer
    from .exporter import export_to_file, export_to_json
    from .llm import get_provider
    
    # Load repos from cache
    cache_path = Path(args.input or f"data/{args.username}_starred.json")
    if not cache_path.exists():
        logger.error(f"Cache not found: {cache_path}. Run 'fetch' first.")
        return 1
    
    with open(cache_path) as f:
        data = json.load(f)
        repos = [Repository.from_dict(r) for r in data]
    
    logger.info(f"Loaded {len(repos)} repos from cache")
    
    # Initialize LLM
    try:
        llm = get_provider(
            provider_name=args.provider,
            api_key=args.api_key,
            model=args.model,
        )
    except ValueError as e:
        logger.error(str(e))
        return 1
    
    # Categorize
    categorizer = Categorizer(llm)
    
    categories = None
    if args.categories:
        # Load custom categories from JSON file
        with open(args.categories) as f:
            cats_data = json.load(f)
            categories = [(c["name"], c.get("description", "")) for c in cats_data]
    
    result = categorizer.categorize_all(
        repos,
        categories=categories,
        preferences=args.preferences or "",
        batch_size=args.batch_size,
    )
    
    # Export results
    output_dir = Path(args.output_dir or ".")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Markdown
    md_path = output_dir / "STARRED_REPOS.md"
    export_to_file(result, md_path)
    
    # JSON (for syncing)
    json_path = output_dir / "starred_data.json"
    export_to_json(result, json_path)
    
    logger.info(f"Categorization complete! Files saved to {output_dir}")
    return 0


def cmd_update_readme(args):
    """Update a README file with starred repos section."""
    from .models import CategorizedRepos, Category, Repository
    from .exporter import update_readme, create_placeholder_readme
    
    # Load categorized data
    data_path = Path(args.data or "starred_data.json")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Run 'categorize' first.")
        return 1
    
    with open(data_path) as f:
        data = json.load(f)
    
    # Reconstruct CategorizedRepos
    categorized = CategorizedRepos(
        generated_at=datetime.fromisoformat(data["generated_at"]),
        llm_provider=data.get("llm_provider", ""),
        llm_model=data.get("llm_model", ""),
    )
    
    for name, cat_data in data.get("categories", {}).items():
        category = Category(
            name=name,
            description=cat_data.get("description", ""),
        )
        for repo_name in cat_data.get("repos", []):
            repo_data = data.get("repositories", {}).get(repo_name, {"full_name": repo_name})
            category.repos.append(Repository.from_dict(repo_data))
        categorized.categories[name] = category
    
    # Update README
    readme_path = Path(args.readme)
    
    if args.create_template:
        create_placeholder_readme(readme_path)
        logger.info(f"Created template README at {readme_path}")
        return 0
    
    success = update_readme(
        readme_path,
        categorized,
        max_repos=args.max_repos,
        max_categories=args.max_categories,
        create_if_missing=args.create,
    )
    
    return 0 if success else 1


def cmd_sync(args):
    """Sync categorization with GitHub star lists."""
    from .github import GitHubListsClient
    from .sync import ListSyncer, sync_from_markdown
    from .models import CategorizedRepos, Category, Repository
    
    if not args.cookie:
        logger.error(
            "GitHub cookie required for list management. "
            "Set GH_COOKIE or use --cookie. "
            "See README for instructions on getting the cookie."
        )
        return 1
    
    # Initialize client
    client = GitHubListsClient(args.username, args.cookie)
    
    # Verify cookie
    if not client.verify_cookie():
        logger.error("Cookie appears to be invalid or expired. Please get a fresh cookie.")
        return 1
    
    # Load data
    if args.from_markdown:
        md_path = Path(args.from_markdown)
        if not md_path.exists():
            logger.error(f"Markdown file not found: {md_path}")
            return 1
        
        results = sync_from_markdown(md_path, client, dry_run=args.dry_run)
    else:
        data_path = Path(args.data or "starred_data.json")
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}. Run 'categorize' first.")
            return 1
        
        with open(data_path) as f:
            data = json.load(f)
        
        # Reconstruct CategorizedRepos
        categorized = CategorizedRepos(
            generated_at=datetime.fromisoformat(data["generated_at"]),
        )
        
        for name, cat_data in data.get("categories", {}).items():
            category = Category(name=name)
            for repo_name in cat_data.get("repos", []):
                repo_data = data.get("repositories", {}).get(repo_name, {"full_name": repo_name})
                category.repos.append(Repository.from_dict(repo_data))
            categorized.categories[name] = category
        
        syncer = ListSyncer(client)
        results = syncer.execute_sync(
            categorized,
            dry_run=args.dry_run,
            delete_unmanaged=args.delete_unmanaged,
            reset_all=args.reset,
        )
    
    if args.dry_run:
        logger.info("Dry run complete. No changes were made.")
    
    return 0 if not results.get("failed") else 1


def cmd_list_providers(args):
    """List available LLM providers."""
    from .llm import list_providers, PROVIDERS
    
    print("\nAvailable LLM Providers:")
    print("=" * 50)
    
    for name in list_providers():
        provider_class = PROVIDERS[name]
        env_key = provider_class.get_env_key()
        models = provider_class.get_available_models()
        
        has_key = "✓" if os.environ.get(env_key) else "✗"
        
        print(f"\n{name.upper()} [{has_key} {env_key}]")
        print(f"  Default model: {provider_class.default_model}")
        print(f"  Available models: {', '.join(models[:5])}")
        if len(models) > 5:
            print(f"                    ...and {len(models) - 5} more")
    
    print("\n" + "=" * 50)
    print("Set the appropriate API key environment variable to use a provider.")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="starred",
        description="AI-powered GitHub Stars Organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch and categorize (auto-detect LLM provider)
  starred fetch --username myuser
  starred categorize --preferences "Focus on DevOps and AI tools"

  # Use specific LLM provider
  starred categorize --provider openai --model gpt-4o

  # Update profile README
  starred update-readme --readme ../myuser/README.md --max-repos 30

  # Sync with GitHub lists (requires cookie)
  starred sync --cookie "$GH_COOKIE" --dry-run
  starred sync --cookie "$GH_COOKIE"

Environment Variables:
  GH_TOKEN           GitHub Personal Access Token
  GH_COOKIE          GitHub browser cookie (for list management)
  ANTHROPIC_API_KEY  Anthropic Claude API key
  OPENAI_API_KEY     OpenAI API key
  GEMINI_API_KEY     Google Gemini API key
        """,
    )
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch starred repositories")
    fetch_parser.add_argument("--token", default=os.environ.get("GH_TOKEN"), help="GitHub token")
    fetch_parser.add_argument("--username", default=os.environ.get("GH_USERNAME"), help="GitHub username")
    fetch_parser.add_argument("--max-repos", type=int, help="Maximum repos to fetch")
    fetch_parser.add_argument("--with-readme", action="store_true", help="Fetch README excerpts")
    fetch_parser.add_argument("--output", "-o", help="Output file path")
    
    # Categorize command
    cat_parser = subparsers.add_parser("categorize", help="Categorize repositories using AI")
    cat_parser.add_argument("--input", "-i", help="Input JSON file (from fetch)")
    cat_parser.add_argument("--username", default=os.environ.get("GH_USERNAME"), help="GitHub username")
    cat_parser.add_argument("--output-dir", "-o", help="Output directory")
    cat_parser.add_argument("--provider", help="LLM provider (anthropic, openai, gemini)")
    cat_parser.add_argument("--api-key", help="LLM API key (or use env var)")
    cat_parser.add_argument("--model", help="LLM model name")
    cat_parser.add_argument("--preferences", "-p", help="Categorization preferences")
    cat_parser.add_argument("--categories", help="JSON file with custom categories")
    cat_parser.add_argument("--batch-size", type=int, default=25, help="Repos per LLM call")
    
    # Update README command
    readme_parser = subparsers.add_parser("update-readme", help="Update README with starred repos")
    readme_parser.add_argument("--readme", "-r", required=True, help="Path to README.md")
    readme_parser.add_argument("--data", "-d", help="Path to starred_data.json")
    readme_parser.add_argument("--max-repos", type=int, default=50, help="Max repos to show")
    readme_parser.add_argument("--max-categories", type=int, default=10, help="Max categories")
    readme_parser.add_argument("--create", action="store_true", help="Create README if missing")
    readme_parser.add_argument("--create-template", action="store_true", help="Create template README")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync with GitHub star lists")
    sync_parser.add_argument("--username", default=os.environ.get("GH_USERNAME"), help="GitHub username")
    sync_parser.add_argument("--cookie", default=os.environ.get("GH_COOKIE"), help="GitHub cookie")
    sync_parser.add_argument("--data", "-d", help="Path to starred_data.json")
    sync_parser.add_argument("--from-markdown", help="Sync from STARRED_REPOS.md instead")
    sync_parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    sync_parser.add_argument("--delete-unmanaged", action="store_true", help="Delete lists not in data")
    sync_parser.add_argument("--reset", action="store_true", help="Delete all lists first")
    
    # List providers command
    subparsers.add_parser("providers", help="List available LLM providers")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Route to command handler
    commands = {
        "fetch": cmd_fetch,
        "categorize": cmd_categorize,
        "update-readme": cmd_update_readme,
        "sync": cmd_sync,
        "providers": cmd_list_providers,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
