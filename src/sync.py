"""Sync categorized repos with GitHub star lists."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from .models import CategorizedRepos, Repository
from .github import GitHubListsClient

logger = logging.getLogger(__name__)


def slugify(name: str) -> str:
    """Convert category name to URL-safe slug."""
    # Remove emoji
    slug = re.sub(r'[^\w\s-]', '', name)
    # Convert to lowercase and replace spaces with hyphens
    slug = slug.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    return slug


class ListSyncer:
    """Sync categorized repos with GitHub star lists."""
    
    def __init__(self, lists_client: GitHubListsClient):
        """
        Initialize the syncer.
        
        Args:
            lists_client: GitHub lists client instance
        """
        self.client = lists_client
    
    def get_current_state(self) -> dict[str, list[str]]:
        """
        Get current state of all GitHub lists.
        
        Returns:
            Dict mapping list slug to list of repo full names
        """
        state = {}
        lists = self.client.get_lists()
        
        for lst in lists:
            slug = lst["slug"]
            repos = self.client.get_list_repos(slug)
            state[slug] = repos
            logger.debug(f"List '{slug}': {len(repos)} repos")
        
        return state
    
    def plan_sync(
        self,
        categorized: CategorizedRepos,
        current_state: Optional[dict[str, list[str]]] = None,
        delete_unmanaged: bool = False,
    ) -> dict:
        """
        Plan what changes need to be made to sync GitHub lists.
        
        Args:
            categorized: Target categorization
            current_state: Current GitHub lists state (fetched if None)
            delete_unmanaged: Delete lists not in categorization
        
        Returns:
            Dict with planned changes
        """
        if current_state is None:
            current_state = self.get_current_state()
        
        plan = {
            "lists_to_create": [],
            "lists_to_delete": [],
            "lists_to_update": {},
            "no_change": [],
        }
        
        # Build target state
        target_state = {}
        for name, category in categorized.categories.items():
            if category.count == 0:
                continue
            slug = slugify(name)
            target_state[slug] = {
                "name": name,
                "repos": [r.full_name for r in category.repos],
            }
        
        # Find lists to create
        for slug, data in target_state.items():
            if slug not in current_state:
                plan["lists_to_create"].append({
                    "slug": slug,
                    "name": data["name"],
                    "repos": data["repos"],
                })
        
        # Find lists to update
        for slug, data in target_state.items():
            if slug in current_state:
                current_repos = set(current_state[slug])
                target_repos = set(data["repos"])
                
                if current_repos != target_repos:
                    plan["lists_to_update"][slug] = {
                        "name": data["name"],
                        "add": list(target_repos - current_repos),
                        "remove": list(current_repos - target_repos),
                    }
                else:
                    plan["no_change"].append(slug)
        
        # Find lists to delete (if enabled)
        if delete_unmanaged:
            managed_slugs = set(target_state.keys())
            for slug in current_state:
                if slug not in managed_slugs:
                    plan["lists_to_delete"].append(slug)
        
        return plan
    
    def execute_sync(
        self,
        categorized: CategorizedRepos,
        dry_run: bool = False,
        delete_unmanaged: bool = False,
        reset_all: bool = False,
    ) -> dict:
        """
        Execute sync between categorization and GitHub lists.
        
        Args:
            categorized: Target categorization
            dry_run: Only plan, don't execute
            delete_unmanaged: Delete lists not in categorization
            reset_all: Delete all existing lists first
        
        Returns:
            Sync results
        """
        results = {
            "created": [],
            "updated": [],
            "deleted": [],
            "failed": [],
            "dry_run": dry_run,
        }
        
        # Reset if requested
        if reset_all and not dry_run:
            logger.warning("Resetting all existing lists...")
            current_lists = self.client.get_lists()
            for lst in current_lists:
                if self.client.delete_list(lst["slug"]):
                    results["deleted"].append(lst["slug"])
                else:
                    results["failed"].append(f"delete:{lst['slug']}")
        
        # Get plan
        current_state = {} if reset_all else None
        plan = self.plan_sync(categorized, current_state, delete_unmanaged)
        
        if dry_run:
            logger.info("DRY RUN - no changes will be made")
            logger.info(f"Would create {len(plan['lists_to_create'])} lists")
            logger.info(f"Would update {len(plan['lists_to_update'])} lists")
            logger.info(f"Would delete {len(plan['lists_to_delete'])} lists")
            return {"plan": plan, **results}
        
        # Create new lists
        for lst_data in plan["lists_to_create"]:
            logger.info(f"Creating list: {lst_data['name']}")
            
            if self.client.create_list(lst_data["name"]):
                results["created"].append(lst_data["slug"])
                
                # Add repos to new list
                for repo in lst_data["repos"]:
                    self.client.add_repo_to_list(lst_data["slug"], repo)
            else:
                results["failed"].append(f"create:{lst_data['slug']}")
        
        # Update existing lists
        for slug, changes in plan["lists_to_update"].items():
            logger.info(f"Updating list: {slug} (+{len(changes['add'])} -{len(changes['remove'])})")
            
            success = True
            for repo in changes["add"]:
                if not self.client.add_repo_to_list(slug, repo):
                    success = False
            
            for repo in changes["remove"]:
                if not self.client.remove_repo_from_list(slug, repo):
                    success = False
            
            if success:
                results["updated"].append(slug)
            else:
                results["failed"].append(f"update:{slug}")
        
        # Delete unmanaged lists
        for slug in plan["lists_to_delete"]:
            logger.info(f"Deleting list: {slug}")
            
            if self.client.delete_list(slug):
                results["deleted"].append(slug)
            else:
                results["failed"].append(f"delete:{slug}")
        
        # Summary
        logger.info(
            f"Sync complete: "
            f"{len(results['created'])} created, "
            f"{len(results['updated'])} updated, "
            f"{len(results['deleted'])} deleted, "
            f"{len(results['failed'])} failed"
        )
        
        return results


def sync_from_markdown(
    markdown_path: Path,
    lists_client: GitHubListsClient,
    dry_run: bool = False,
) -> dict:
    """
    Sync GitHub lists from a STARRED_REPOS.md file.
    
    Args:
        markdown_path: Path to STARRED_REPOS.md
        lists_client: GitHub lists client
        dry_run: Only plan, don't execute
    
    Returns:
        Sync results
    """
    # Parse markdown to extract categories and repos
    content = markdown_path.read_text(encoding="utf-8")
    
    categorized = CategorizedRepos()
    current_category = None
    
    for line in content.split("\n"):
        # Match category headers (## Emoji Name)
        if line.startswith("## "):
            cat_name = line[3:].strip()
            if cat_name and not cat_name.startswith("📑"):  # Skip TOC
                from .models import Category
                current_category = Category(name=cat_name)
                categorized.categories[cat_name] = current_category
        
        # Match repo links
        elif current_category and "[" in line and "github.com" in line:
            match = re.search(r'\[([^\]]+)\]\(https://github\.com/([^)]+)\)', line)
            if match:
                full_name = match.group(2)
                if "/" in full_name:
                    repo = Repository(
                        full_name=full_name,
                        name=full_name.split("/")[1],
                        owner=full_name.split("/")[0],
                        url=f"https://github.com/{full_name}",
                    )
                    current_category.repos.append(repo)
    
    logger.info(f"Parsed {categorized.total_repos} repos in {categorized.category_count} categories from markdown")
    
    # Sync
    syncer = ListSyncer(lists_client)
    return syncer.execute_sync(categorized, dry_run=dry_run)
