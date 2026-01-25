# ⭐ Starred

**AI-powered GitHub Stars Organizer**

Automatically categorize your GitHub starred repositories using AI (Claude, GPT, or Gemini), export to Markdown, and optionally sync with GitHub star lists.

[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/yourusername/starred/update-starred.yml?label=auto-update)](https://github.com/yourusername/starred/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🤖 **Multi-LLM Support** - Use Anthropic Claude, OpenAI GPT, or Google Gemini
- 📝 **Markdown Export** - Generate beautiful `STARRED_REPOS.md` organized by category
- 👤 **Profile README Integration** - Auto-update your GitHub profile README with starred repos
- 🔄 **GitHub Lists Sync** - Sync categories to actual GitHub star lists (local mode)
- ⚡ **GitHub Actions** - Automated daily updates
- 🎯 **Customizable Categories** - Define your own categories or let AI generate them
- 📊 **Smart Categorization** - Uses repo description, language, topics, and README

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended)

1. **Fork this repository** or use it as a template

2. **Add secrets** in Settings → Secrets → Actions:
   
   | Secret | Required | Description |
   |--------|----------|-------------|
   | `GH_PAT` | Yes | GitHub Personal Access Token |
   | `ANTHROPIC_API_KEY` | Pick one | Anthropic Claude API key |
   | `OPENAI_API_KEY` | Pick one | OpenAI API key |
   | `GEMINI_API_KEY` | Pick one | Google Gemini API key |

3. **Run the workflow** manually or wait for the daily schedule

4. **View results** in `STARRED_REPOS.md`

### Option 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/starred.git
cd starred

# Install with your preferred LLM provider
pip install -e ".[anthropic]"  # For Claude
pip install -e ".[openai]"     # For GPT
pip install -e ".[gemini]"     # For Gemini
pip install -e ".[all]"        # For all providers

# Set environment variables
export GH_TOKEN="ghp_xxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxx"  # Or OPENAI_API_KEY or GEMINI_API_KEY

# Run
starred fetch --username yourusername
starred categorize --preferences "Focus on DevOps, AI, and web development"
```

## 📖 Usage

### Commands

```bash
# Fetch starred repositories
starred fetch [--username USER] [--with-readme] [--max-repos N]

# Categorize using AI
starred categorize [--provider anthropic|openai|gemini] [--preferences "..."]

# Update a profile README
starred update-readme --readme /path/to/README.md [--max-repos 50]

# Sync with GitHub lists (requires cookie)
starred sync --cookie "$GH_COOKIE" [--dry-run]

# List available LLM providers
starred providers
```

### Custom Categories

Create a `categories.json` file:

```json
[
  {"name": "🤖 AI & ML", "description": "Machine learning and AI tools"},
  {"name": "🌐 Web Dev", "description": "Web development frameworks"},
  {"name": "⚙️ DevOps", "description": "Infrastructure and automation"}
]
```

Then use it:

```bash
starred categorize --categories categories.json
```

### Custom Preferences

Tell the AI how to organize your repos:

```bash
starred categorize --preferences "
I'm a backend developer focused on Go and Python.
Create categories for:
- Microservices and distributed systems
- Database tools and ORMs
- API development
- Testing frameworks
- Security tools
Skip frontend and mobile categories.
"
```

## 👤 Profile README Integration

Add these placeholder tags to your profile README (`username/username/README.md`):

```markdown
## ⭐ My Starred Repositories

<!-- STARRED_REPOS_START -->
<!-- This section is auto-updated by Starred -->
<!-- STARRED_REPOS_END -->
```

Then either:

1. **Use the GitHub Action** - Set up the `update-profile-readme.yml` workflow
2. **Run locally** - `starred update-readme --readme /path/to/README.md`

The section between the tags will be automatically updated with your categorized starred repos.

## 🔄 GitHub Lists Sync

> ⚠️ **Note**: GitHub has no official API for star lists. This feature uses browser cookies which expire every ~2 weeks.

To sync your categorization with actual GitHub star lists:

### Getting the Cookie

1. Go to `https://github.com/yourusername?tab=stars`
2. Open DevTools (F12) → Network tab
3. Refresh the page
4. Click the first request
5. Copy the `Cookie` header value

### Syncing

```bash
# Preview changes (dry run)
starred sync --cookie "$GH_COOKIE" --dry-run

# Apply changes
starred sync --cookie "$GH_COOKIE"

# Reset all lists and recreate
starred sync --cookie "$GH_COOKIE" --reset

# Sync from existing STARRED_REPOS.md
starred sync --from-markdown STARRED_REPOS.md --cookie "$GH_COOKIE"
```

## 🤖 LLM Providers

| Provider | Env Variable | Default Model | Notes |
|----------|--------------|---------------|-------|
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4 | Best quality |
| OpenAI | `OPENAI_API_KEY` | gpt-4o | JSON mode support |
| Gemini | `GEMINI_API_KEY` | gemini-2.0-flash | Free tier available |

The tool auto-detects which provider to use based on available API keys.

```bash
# Force specific provider
starred categorize --provider openai --model gpt-4o-mini
```

## 📁 Output Files

| File | Description |
|------|-------------|
| `STARRED_REPOS.md` | Beautiful Markdown with all categorized repos |
| `starred_data.json` | JSON data for syncing and README updates |
| `data/starred_cache.json` | Cached repo data from GitHub API |

## ⚙️ Configuration

### Environment Variables

```bash
# Required
GH_TOKEN=ghp_xxxx              # GitHub Personal Access Token

# LLM Provider (at least one required for categorization)
ANTHROPIC_API_KEY=sk-ant-xxxx  # Anthropic Claude
OPENAI_API_KEY=sk-xxxx         # OpenAI
GEMINI_API_KEY=xxxx            # Google Gemini

# Optional
GH_USERNAME=yourusername       # Your GitHub username
GH_COOKIE=...                  # For list sync (local mode only)
```

### GitHub Actions Secrets

| Secret | Description |
|--------|-------------|
| `GH_PAT` | GitHub PAT with `repo` scope |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Gemini API key |
| `PROFILE_REPO_TOKEN` | PAT for profile repo (if different from starred repo) |

## 🔧 GitHub Actions Workflows

### `update-starred.yml`

Runs daily to:
1. Fetch your starred repos
2. Categorize using AI
3. Update `STARRED_REPOS.md`
4. Commit changes

### `update-profile-readme.yml`

Triggered when `STARRED_REPOS.md` changes:
1. Checks out your profile repo
2. Updates README.md between placeholder tags
3. Commits changes

## 🛠️ Development

```bash
# Clone and install dev dependencies
git clone https://github.com/yourusername/starred.git
cd starred
pip install -e ".[dev,all]"

# Run tests
pytest

# Format code
black src/
ruff check src/ --fix

# Type checking
mypy src/
```

## 📊 Example Output

See [STARRED_REPOS.md](STARRED_REPOS.md) for a live example of the generated output.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Ideas for Contributions

- [ ] Additional LLM providers (Ollama, local models)
- [ ] Better category emoji detection
- [ ] Obsidian/Notion export formats
- [ ] Web UI for category management
- [ ] Browser extension for cookie refresh

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Credits

Inspired by:
- [StarListify](https://github.com/nhtlongcs/StarListify)
- [github-starred-list](https://github.com/haile01/github-starred-list)

Built with ❤️ using Claude, GPT, and Gemini.

---

<p align="center">
  <a href="https://github.com/yourusername/starred/stargazers">⭐ Star this repo</a> if you find it useful!
</p>
