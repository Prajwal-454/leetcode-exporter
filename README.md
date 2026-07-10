# 🚀 LeetCode Exporter

Automatically download **all** your accepted LeetCode solutions and push them to a GitHub repository — with beautiful READMEs, statistics, and incremental sync.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LeetCode](https://img.shields.io/badge/LeetCode-FFA116?style=for-the-badge&logo=leetcode&logoColor=black)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

</div>

## ✨ Features

- 📥 **Download all accepted solutions** from LeetCode via GraphQL API
- 🔄 **Incremental sync** — only download new or updated submissions
- 📂 **Organized folder structure** — `0001-Two-Sum/0001-Two-Sum.py`
- 📝 **Auto-generated READMEs** per problem (difficulty, tags, links, date)
- 📊 **Repository-level README** with stats table, badges, and problem list
- 🌐 **Multi-language support** — Python, Java, C++, Go, Rust, JS, and 15+ more
- 🔀 **Git integration** — auto-init, commit, and push to GitHub
- 📈 **CSV export** of all solved problems
- 🎨 **Rich terminal UI** with progress bars and color output
- ♻️ **Retry logic** for resilient API communication

## 📁 Project Structure

```
leetcode-exporter/
├── main.py              # CLI entry point and orchestrator
├── api.py               # LeetCode GraphQL API client
├── github.py            # Git repository management
├── config.py            # Configuration and constants
├── utils.py             # Helpers: naming, README generation, CSV export
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── .env.example         # Template for environment variables
```

## 🛠️ Installation

### Prerequisites

- **Python 3.10+**
- **Git** installed and on your PATH
- A **GitHub repository** (create one at https://github.com/new)

### Steps

1. **Clone or download this project**

   ```bash
   git clone <this-repo-url>
   cd leetcode-exporter
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your values (see [Configuration](#-configuration)).

## 🔑 Configuration

Create a `.env` file (or copy from `.env.example`):

```env
# Required — LeetCode session cookies
LEETCODE_SESSION=your_session_cookie_here
CSRFTOKEN=your_csrf_token_here

# Optional — GitHub integration
GITHUB_REPO=https://github.com/USERNAME/LeetCode.git
GITHUB_BRANCH=main

# Optional — output directory
OUTPUT_FOLDER=LeetCode
```

### How to get your LeetCode cookies

1. Open [leetcode.com](https://leetcode.com) and log in
2. Open **Developer Tools** (F12 or Ctrl+Shift+I)
3. Go to **Application** → **Cookies** → `https://leetcode.com`
4. Copy the values of:
   - `LEETCODE_SESSION`
   - `csrftoken`

> ⚠️ **Security**: Never share or commit your `.env` file. It is already listed in `.gitignore`.

## 🚀 Usage

### Full Sync — Download Everything

```bash
python main.py
```

Downloads **all** your accepted solutions, generates READMEs, exports CSV, and pushes to GitHub.

### Incremental Sync — Only New Solutions

```bash
python main.py --sync
```

Checks for new or updated submissions since the last run and downloads only those.

### Custom `.env` File

```bash
python main.py --env path/to/.env.prod
```

### Help

```bash
python main.py --help
```

## 📂 Output Structure

After running, your output folder will look like:

```
LeetCode/
├── README.md                    # Repository-level summary
├── solutions.csv                # CSV export of all problems
├── .leetcode_meta.json          # Sync metadata (for incremental mode)
├── 0001-Two-Sum/
│   ├── 0001-Two-Sum.py
│   └── README.md
├── 0002-Add-Two-Numbers/
│   ├── 0002-Add-Two-Numbers.java
│   └── README.md
├── 0003-Longest-Substring.../
│   ├── 0003-Longest-Substring....cpp
│   └── README.md
└── ...
```

### Per-Problem README Includes

| Field | Description |
|-------|-------------|
| Title | Problem number and name |
| Difficulty | Easy / Medium / Hard with colored badge |
| Tags | Topic tags from LeetCode |
| Language | Programming language used |
| URL | Direct link to the problem |
| Date Solved | Submission date |

## 🌐 Supported Languages

| Language | Extension | Language | Extension |
|----------|-----------|----------|-----------|
| Python | `.py` | Go | `.go` |
| Java | `.java` | Ruby | `.rb` |
| C++ | `.cpp` | Swift | `.swift` |
| C | `.c` | Kotlin | `.kt` |
| C# | `.cs` | Rust | `.rs` |
| JavaScript | `.js` | Scala | `.scala` |
| TypeScript | `.ts` | PHP | `.php` |
| Dart | `.dart` | Bash | `.sh` |
| SQL (MySQL, PostgreSQL, etc.) | `.sql` | Elixir | `.ex` |

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `LEETCODE_SESSION is required` | Fill in your cookies in `.env` |
| `No solved problems found` | Your session cookie may have expired — get a new one |
| `Push failed` | Ensure your GitHub repo exists and you have push access |
| `GraphQL errors` | LeetCode may be rate-limiting — the retry logic handles most cases |

## 📄 License

This project is provided as-is for personal use. Use responsibly and respect LeetCode's Terms of Service.
