# ⭐ Starred — AI-Powered GitHub Stars Organizer

> **Automatically categorize, organize, and showcase your GitHub starred repositories using AI (Claude, GPT-4, Gemini)**

[![GitHub Stars](https://img.shields.io/github/stars/amirhmoradi/starred?style=social)](https://github.com/amirhmoradi/starred/stargazers)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/amirhmoradi/starred/update-starred.yml?label=auto-update)](https://github.com/amirhmoradi/starred/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Starred** transforms your messy GitHub stars into a beautifully organized, AI-categorized collection. Perfect for developers who star repos and forget about them!

[🚀 Quick Start](#-quick-start) • [📸 Examples](#-example-output) • [🤖 AI Providers](#-supported-ai-providers) • [📖 Documentation](#-cli-reference)

---

## 🎯 Why Starred?

**The Problem:** You've starred hundreds of GitHub repositories. Finding that Docker tool or that React library you starred months ago? Nearly impossible.

**The Solution:** Let AI organize your stars automatically.

| Before Starred | After Starred |
|----------------|---------------|
| 500+ unorganized stars | Neatly categorized by topic |
| "Where's that CLI tool?" | Searchable markdown docs |
| Empty profile README | Auto-updated showcase |
| Manual GitHub Lists | AI-synced categories |

---

## ✨ Key Features

### 🤖 Multi-AI Support
Use **Claude**, **GPT-4**, or **Gemini** to intelligently categorize repositories based on description, language, topics, and README content.

### 📝 Markdown Export
Generates a beautiful `STARRED_REPOS.md` with table of contents, categories, star counts, and descriptions.

### 👤 Profile README Integration
Automatically updates your GitHub profile README with a curated showcase of your starred repos.

### 🔄 GitHub Actions Automation
Set it and forget it — runs daily to keep your collection organized as you star new repos.

### 📊 GitHub Lists Sync
Optionally sync your AI-generated categories to native GitHub Star Lists.

### 🎨 Fully Customizable
Define your own categories, preferences, and display options.

---

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended — 5 minutes)

1. **Fork or use this template**
   
   [![Fork](https://img.shields.io/badge/Fork-Repository-blue?style=for-the-badge&logo=github)](https://github.com/amirhmoradi/starred/fork)
   [![Use Template](https://img.shields.io/badge/Use-Template-green?style=for-the-badge&logo=github)](https://github.com/new?template_name=starred&template_owner=amirhmoradi)

2. **Add secrets** in Settings → Secrets → Actions:
   
   | Secret | Required | Get it from |
   |--------|----------|-------------|
   | `GH_PAT` | ✅ | [Create PAT](https://github.com/settings/personal-access-tokens/new) with `starring:read` |
   | `ANTHROPIC_API_KEY` | Pick one | [Anthropic Console](https://console.anthropic.com/) |
   | `OPENAI_API_KEY` | Pick one | [OpenAI Platform](https://platform.openai.com/api-keys) |
   | `GEMINI_API_KEY` | Pick one | [Google AI Studio](https://aistudio.google.com/apikey) (**Free!**) |

3. **Run the workflow**: Actions → Update Starred Repos → Run workflow

4. **Check results** in `STARRED_REPOS.md` ✨

### Option 2: Local / CLI Installation

```bash
# Install from source
git clone https://github.com/amirhmoradi/starred.git
cd starred
pip install -e ".[all]"

# Set environment variables
export GH_TOKEN="ghp_your_token"
export ANTHROPIC_API_KEY="sk-ant-xxx"  # or OPENAI_API_KEY or GEMINI_API_KEY

# Fetch your stars
starred fetch --username YOUR_USERNAME

# Categorize with AI
starred categorize --preferences "Focus on DevOps, AI tools, and web development"

# See your organized stars!
cat STARRED_REPOS.md
```

---

## 📸 Example Output

### STARRED_REPOS.md Preview

```markdown
# ⭐ My Starred Repositories

**847** repositories organized into **18** categories

## 📑 Table of Contents
- [🤖 AI & Machine Learning](#-ai--machine-learning) (142)
- [🌐 Web Development](#-web-development) (98)
- [⚙️ DevOps & Infrastructure](#-devops--infrastructure) (87)
- [🔧 CLI Tools](#-cli-tools) (64)
...

## 🤖 AI & Machine Learning
*Machine learning frameworks, LLMs, AI tools and utilities*

- [langchain-ai/langchain](https://github.com/langchain-ai/langchain) `Python` ⭐ 95,000 - Build LLM applications
- [openai/whisper](https://github.com/openai/whisper) `Python` ⭐ 72,000 - Speech recognition
- [ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp) `C++` ⭐ 68,000 - Run LLMs locally
...
```

### Profile README Integration

Your GitHub profile automatically displays:

```markdown
### 🤖 AI & Machine Learning
- [langchain-ai/langchain](https://github.com/langchain-ai/langchain) `Python` ⭐ 95,000
- [openai/whisper](https://github.com/openai/whisper) `Python` ⭐ 72,000

### ⚙️ DevOps & Infrastructure  
- [docker/compose](https://github.com/docker/compose) `Go` ⭐ 34,000
- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes) `Go` ⭐ 112,000

*[View all 847 repositories →](STARRED_REPOS.md)*
```

---

## 🤖 Supported AI Providers

| Provider | Model | Cost | Speed | Quality |
|----------|-------|------|-------|---------|
| **Anthropic** | Claude Sonnet 4 | ~$0.02/run | Fast | ⭐⭐⭐⭐⭐ |
| **OpenAI** | GPT-4o | ~$0.03/run | Fast | ⭐⭐⭐⭐⭐ |
| **Google** | Gemini 2.0 Flash | **Free tier!** | Very Fast | ⭐⭐⭐⭐ |

The tool **auto-detects** which provider to use based on available API keys.

```bash
# Force a specific provider
starred categorize --provider gemini --model gemini-2.0-flash
starred categorize --provider openai --model gpt-4o-mini
starred categorize --provider anthropic --model claude-sonnet-4-20250514
```

---

## 👤 Profile README Setup

1. **Add placeholder tags** to your profile repo (`username/username/README.md`):

```markdown
## ⭐ My Starred Repositories

<!-- STARRED_REPOS_START -->
<!-- Auto-generated content will appear here -->
<!-- STARRED_REPOS_END -->
```

2. **Enable the workflow** — the "Update Profile README" action will automatically:
   - Update the section between the tags
   - Copy the full `STARRED_REPOS.md` to your profile repo
   - Add a link to view all stars

---

## 🔄 GitHub Lists Sync (Advanced)

Sync AI categories to **native GitHub Star Lists**:

> ⚠️ Requires browser cookie (GitHub has no official API for lists)

```bash
# Preview changes
starred sync --cookie "$GH_COOKIE" --dry-run

# Apply changes
starred sync --cookie "$GH_COOKIE"

# Reset and recreate all lists
starred sync --cookie "$GH_COOKIE" --reset
```

<details>
<summary><strong>How to get the cookie</strong></summary>

1. Go to `https://github.com/yourusername?tab=stars`
2. Open DevTools (F12) → Network tab
3. Refresh the page
4. Click the first request → Headers
5. Copy the `Cookie` value

Note: Cookies expire every ~2 weeks.

</details>

---

## ⚙️ Configuration Options

### Custom Categories

Create `categories.json`:

```json
[
  {"name": "🤖 AI & ML", "description": "Machine learning and AI tools"},
  {"name": "🏠 Self-Hosted", "description": "Self-hosted alternatives to SaaS"},
  {"name": "🚀 Starter Kits", "description": "Boilerplates and templates"}
]
```

```bash
starred categorize --categories categories.json
```

### AI Preferences

Guide the AI with natural language:

```bash
starred categorize --preferences "
I'm a DevOps engineer focused on Kubernetes.
Create categories for:
- Container orchestration
- CI/CD pipelines
- Monitoring & observability
- Infrastructure as Code
Skip frontend and mobile categories.
"
```

### Environment Variables

```bash
# Required
GH_TOKEN=ghp_xxxx              # GitHub Personal Access Token

# LLM Provider (at least one)
ANTHROPIC_API_KEY=sk-ant-xxxx  # Anthropic Claude
OPENAI_API_KEY=sk-xxxx         # OpenAI GPT
GEMINI_API_KEY=xxxx            # Google Gemini (free tier available!)

# Optional
GH_USERNAME=yourusername       # Auto-detected if not set
GH_COOKIE=...                  # For GitHub Lists sync
```

---

## 📖 CLI Reference

```
starred --help

Commands:
  fetch          Fetch starred repos from GitHub API
  categorize     Categorize repos using AI
  update-readme  Update README with starred repos section
  sync           Sync with GitHub Star Lists
  providers      List available LLM providers

Options:
  --help         Show help message
  --verbose      Enable debug logging

Examples:
  starred fetch --username myuser --with-readme
  starred categorize --provider gemini --preferences "Focus on Python tools"
  starred update-readme --readme ./README.md --include-toc --max-repos 100
  starred sync --cookie "$COOKIE" --dry-run
```

---

## 🆚 Comparison with Alternatives

| Feature | **Starred** | StarListify | Astral | Manual |
|---------|------------|-------------|--------|--------|
| AI Categorization | ✅ Multi-provider | ⚠️ Gemini only | ❌ | ❌ |
| GitHub Actions | ✅ Full automation | ⚠️ Basic | ❌ | ❌ |
| Profile README | ✅ Auto-update | ❌ | ❌ | ✅ |
| GitHub Lists | ✅ Sync | ✅ | ❌ | ✅ |
| Open Source | ✅ MIT | ✅ MIT | ❌ | — |
| Custom Categories | ✅ | ⚠️ | ❌ | ✅ |
| Multi-LLM | ✅ Claude/GPT/Gemini | ❌ | ❌ | — |

---

## 📊 How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Stars   │────▶│   AI Analysis   │────▶│    Markdown     │
│  (API fetch)    │     │ Claude/GPT/     │     │   Generation    │
│                 │     │ Gemini          │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────┐
                        ▼                               ▼               ▼
               ┌─────────────────┐            ┌─────────────────┐  ┌─────────┐
               │ STARRED_REPOS.md│            │  Profile README │  │ GitHub  │
               │   (full list)   │            │   (summary)     │  │  Lists  │
               └─────────────────┘            └─────────────────┘  └─────────┘
```

1. **Fetch** — Downloads starred repos via GitHub API
2. **Analyze** — AI categorizes based on metadata & README
3. **Generate** — Creates organized Markdown documentation
4. **Deploy** — Updates profile README automatically
5. **Sync** — Creates GitHub Lists (optional)

---

## ❓ FAQ

<details>
<summary><strong>How much does it cost?</strong></summary>

Very affordable:
- **Google Gemini**: Free tier available!
- **Claude/GPT**: ~$0.02-0.05 per run for ~500 stars

</details>

<details>
<summary><strong>How often does it update?</strong></summary>

The GitHub Action runs daily at 2 AM UTC. Customize the cron schedule or run manually anytime.

</details>

<details>
<summary><strong>Can I use my own categories?</strong></summary>

Yes! Create a `categories.json` file or use `--preferences` to guide the AI with natural language.

</details>

<details>
<summary><strong>Is my data safe?</strong></summary>

Only public repository metadata (name, description, language) is sent to the AI. No private data is shared.

</details>

<details>
<summary><strong>Why do GitHub Lists need a cookie?</strong></summary>

GitHub doesn't provide an official API for star lists. The tool uses your browser session (cookie) to manage lists via the web interface.

</details>

<details>
<summary><strong>Does it work with organizations?</strong></summary>

Yes! Set `profile_repo` to `org-name/.github` in the workflow to update an organization's profile.

</details>

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ideas for contributions:**
- [ ] Additional LLM providers (Ollama, local models)
- [ ] Export to Notion, Obsidian, Raindrop.io
- [ ] Web UI for category management
- [ ] Browser extension for cookie refresh
- [ ] Semantic search over starred repos

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Inspired by [StarListify](https://github.com/nhtlongcs/StarListify) and the GitHub community.

---

<p align="center">
  <strong>Found this useful? Give it a ⭐ to help others discover it!</strong>
</p>

<p align="center">
  <a href="https://github.com/amirhmoradi/starred/stargazers">⭐ Star</a> •
  <a href="https://github.com/amirhmoradi/starred/fork">🍴 Fork</a> •
  <a href="https://github.com/amirhmoradi/starred/issues">🐛 Issues</a> •
  <a href="https://github.com/amirhmoradi/starred/discussions">💬 Discuss</a>
</p>

---

<sub>
<strong>Keywords:</strong> github stars organizer, organize github starred repositories, ai categorize github stars, 
github starred repos manager, github profile readme stars, starred repositories markdown, github lists automation, 
claude github stars, gpt github organizer, gemini github, awesome list generator, github star tracker, 
github bookmarks organizer, developer tools, github automation, starred repos to markdown, github stars export,
categorize github stars ai, github stars manager tool, organize github bookmarks
</sub>