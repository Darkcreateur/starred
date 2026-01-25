"""GitHub API client for starred repos and lists management."""

import json
import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Repository

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """GitHub API error."""
    pass


class GitHubClient:
    """Client for GitHub REST API operations."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, username: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub Personal Access Token
            username: GitHub username (will be fetched if not provided)
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.star+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Starred-Repos-Organizer/1.0"
        })
        
        # Fetch username if not provided
        if username:
            self.username = username
        else:
            self.username = self._get_authenticated_user()
    
    def _get_authenticated_user(self) -> str:
        """Get the authenticated user's username."""
        response = self.session.get(f"{self.BASE_URL}/user")
        response.raise_for_status()
        return response.json()["login"]
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a request with rate limit handling."""
        response = self.session.request(method, url, **kwargs)
        
        # Handle rate limiting
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "0")
            if remaining == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                wait_time = max(reset_time - time.time(), 0) + 1
                logger.warning(f"Rate limited. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                return self._make_request(method, url, **kwargs)
        
        response.raise_for_status()
        return response
    
    def get_starred_repos(
        self,
        per_page: int = 100,
        max_repos: Optional[int] = None,
        with_timestamps: bool = True,
    ) -> list[Repository]:
        """
        Fetch all starred repositories for the authenticated user.
        
        Args:
            per_page: Number of repos per page (max 100)
            max_repos: Maximum number of repos to fetch (None for all)
            with_timestamps: Include starred_at timestamp
        
        Returns:
            List of Repository objects
        """
        repos = []
        page = 1
        
        headers = {"Accept": "application/vnd.github.star+json"} if with_timestamps else {}
        
        while True:
            logger.info(f"Fetching starred repos page {page}...")
            
            response = self._make_request(
                "GET",
                f"{self.BASE_URL}/user/starred",
                params={"per_page": per_page, "page": page},
                headers=headers,
            )
            
            data = response.json()
            if not data:
                break
            
            for item in data:
                starred_at = item.get("starred_at") if with_timestamps else None
                repo = Repository.from_api_response(item, starred_at)
                repos.append(repo)
                
                if max_repos and len(repos) >= max_repos:
                    logger.info(f"Reached max_repos limit: {max_repos}")
                    return repos
            
            page += 1
            
            # Check if we've reached the last page
            if len(data) < per_page:
                break
        
        logger.info(f"Fetched {len(repos)} starred repositories")
        return repos
    
    def get_readme(self, full_name: str, max_length: int = 2000) -> Optional[str]:
        """
        Fetch README content for a repository.
        
        Args:
            full_name: Repository full name (owner/repo)
            max_length: Maximum characters to return
        
        Returns:
            README content or None if not found
        """
        try:
            response = self._make_request(
                "GET",
                f"{self.BASE_URL}/repos/{full_name}/readme",
                headers={"Accept": "application/vnd.github.raw"}
            )
            return response.text[:max_length]
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"No README found for {full_name}")
            else:
                logger.debug(f"Error fetching README for {full_name}: {e}")
            return None
    
    def get_rate_limit(self) -> dict:
        """Get current rate limit status."""
        response = self.session.get(f"{self.BASE_URL}/rate_limit")
        return response.json()


class GitHubListsClient:
    """
    Client for managing GitHub star lists.
    
    Uses the unofficial web-based API since GitHub doesn't provide
    a REST API for star lists.
    
    WARNING: This requires a browser cookie and may break if GitHub
    changes their web interface.
    """
    
    BASE_URL = "https://github.com"
    
    def __init__(self, username: str, cookie: str):
        """
        Initialize the lists client.
        
        Args:
            username: GitHub username
            cookie: Browser cookie string from github.com
        """
        self.username = username
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update({
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        self._csrf_token = None
    
    def _get_csrf_token(self) -> str:
        """Extract CSRF token from GitHub page."""
        if self._csrf_token:
            return self._csrf_token
        
        response = self.session.get(f"{self.BASE_URL}/{self.username}?tab=stars")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Look for authenticity token in meta tag or form
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta:
            self._csrf_token = meta.get("content")
            return self._csrf_token
        
        # Try to find in a form
        token_input = soup.find("input", {"name": "authenticity_token"})
        if token_input:
            self._csrf_token = token_input.get("value")
            return self._csrf_token
        
        raise GitHubAPIError("Could not find CSRF token. Cookie may be expired.")
    
    def get_lists(self) -> list[dict]:
        """
        Get all star lists for the user.
        
        Returns:
            List of dicts with 'name', 'slug', 'description', 'count'
        """
        response = self.session.get(f"{self.BASE_URL}/{self.username}?tab=stars")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        lists = []
        
        # Find the lists sidebar
        list_items = soup.select('a[href*="/stars/"][href*="/lists/"]')
        
        for item in list_items:
            href = item.get("href", "")
            if "/lists/" in href:
                # Extract list slug from URL
                match = re.search(r"/lists/([^/]+)", href)
                if match:
                    slug = match.group(1)
                    name = item.get_text(strip=True)
                    # Remove count from name if present
                    name = re.sub(r"\s*\d+\s*$", "", name)
                    lists.append({
                        "name": name,
                        "slug": slug,
                        "url": urljoin(self.BASE_URL, href),
                    })
        
        logger.info(f"Found {len(lists)} existing star lists")
        return lists
    
    def get_list_repos(self, list_slug: str) -> list[str]:
        """
        Get all repositories in a list.
        
        Args:
            list_slug: The list's URL slug
        
        Returns:
            List of repository full names (owner/repo)
        """
        repos = []
        page = 1
        
        while True:
            url = f"{self.BASE_URL}/stars/{self.username}/lists/{list_slug}"
            if page > 1:
                url += f"?page={page}"
            
            response = self.session.get(url)
            if response.status_code == 404:
                break
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Find repo links
            repo_links = soup.select('h3 a[href^="/"]')
            page_repos = []
            
            for link in repo_links:
                href = link.get("href", "").strip("/")
                if "/" in href and not href.startswith("stars/"):
                    page_repos.append(href)
            
            if not page_repos:
                break
            
            repos.extend(page_repos)
            page += 1
        
        return repos
    
    def create_list(self, name: str, description: str = "") -> bool:
        """
        Create a new star list.
        
        Args:
            name: List name (max ~50 chars)
            description: List description
        
        Returns:
            True if successful
        """
        csrf_token = self._get_csrf_token()
        
        # GitHub uses a specific endpoint for creating lists
        url = f"{self.BASE_URL}/stars/{self.username}/lists"
        
        data = {
            "authenticity_token": csrf_token,
            "user_list[name]": name[:50],
            "user_list[description]": description[:255],
        }
        
        response = self.session.post(
            url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml",
            },
            allow_redirects=False,
        )
        
        # Success usually returns a redirect (302)
        if response.status_code in (200, 201, 302):
            logger.info(f"Created list: {name}")
            self._csrf_token = None  # Reset token after mutation
            return True
        
        logger.error(f"Failed to create list '{name}': {response.status_code}")
        return False
    
    def delete_list(self, list_slug: str) -> bool:
        """
        Delete a star list.
        
        Args:
            list_slug: The list's URL slug
        
        Returns:
            True if successful
        """
        csrf_token = self._get_csrf_token()
        
        url = f"{self.BASE_URL}/stars/{self.username}/lists/{list_slug}"
        
        response = self.session.post(
            url,
            data={
                "authenticity_token": csrf_token,
                "_method": "delete",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            allow_redirects=False,
        )
        
        if response.status_code in (200, 302):
            logger.info(f"Deleted list: {list_slug}")
            self._csrf_token = None
            return True
        
        logger.error(f"Failed to delete list '{list_slug}': {response.status_code}")
        return False
    
    def add_repo_to_list(self, list_slug: str, repo_full_name: str) -> bool:
        """
        Add a repository to a star list.
        
        Args:
            list_slug: The list's URL slug
            repo_full_name: Repository full name (owner/repo)
        
        Returns:
            True if successful
        """
        csrf_token = self._get_csrf_token()
        
        # This endpoint is used when clicking the star dropdown
        owner, repo = repo_full_name.split("/")
        url = f"{self.BASE_URL}/{owner}/{repo}/star_lists"
        
        response = self.session.post(
            url,
            data={
                "authenticity_token": csrf_token,
                "list_slug": list_slug,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        
        if response.status_code == 200:
            logger.debug(f"Added {repo_full_name} to list {list_slug}")
            return True
        
        logger.warning(f"Failed to add {repo_full_name} to {list_slug}: {response.status_code}")
        return False
    
    def remove_repo_from_list(self, list_slug: str, repo_full_name: str) -> bool:
        """
        Remove a repository from a star list.
        
        Args:
            list_slug: The list's URL slug
            repo_full_name: Repository full name (owner/repo)
        
        Returns:
            True if successful
        """
        csrf_token = self._get_csrf_token()
        
        owner, repo = repo_full_name.split("/")
        url = f"{self.BASE_URL}/{owner}/{repo}/star_lists/{list_slug}"
        
        response = self.session.post(
            url,
            data={
                "authenticity_token": csrf_token,
                "_method": "delete",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        
        if response.status_code == 200:
            logger.debug(f"Removed {repo_full_name} from list {list_slug}")
            return True
        
        logger.warning(f"Failed to remove {repo_full_name} from {list_slug}: {response.status_code}")
        return False
    
    def sync_list(self, list_slug: str, repos: list[str], create_if_missing: bool = True) -> dict:
        """
        Sync a list to contain exactly the specified repos.
        
        Args:
            list_slug: The list's URL slug
            repos: List of repo full names that should be in the list
            create_if_missing: Create the list if it doesn't exist
        
        Returns:
            Dict with 'added', 'removed', 'unchanged' counts
        """
        # Get current repos in list
        try:
            current = set(self.get_list_repos(list_slug))
        except Exception:
            if create_if_missing:
                # Convert slug to name (replace - with space, title case)
                name = list_slug.replace("-", " ").title()
                self.create_list(name)
                current = set()
            else:
                raise
        
        target = set(repos)
        
        to_add = target - current
        to_remove = current - target
        
        results = {"added": 0, "removed": 0, "unchanged": len(current & target)}
        
        for repo in to_add:
            if self.add_repo_to_list(list_slug, repo):
                results["added"] += 1
        
        for repo in to_remove:
            if self.remove_repo_from_list(list_slug, repo):
                results["removed"] += 1
        
        logger.info(
            f"Synced list '{list_slug}': "
            f"+{results['added']} -{results['removed']} ={results['unchanged']}"
        )
        
        return results
    
    def verify_cookie(self) -> bool:
        """Check if the cookie is still valid."""
        try:
            response = self.session.get(f"{self.BASE_URL}/{self.username}?tab=stars")
            # Check if we're logged in by looking for profile elements
            return "Sign out" in response.text or "logged_in=yes" in self.cookie
        except Exception as e:
            logger.error(f"Cookie verification failed: {e}")
            return False
