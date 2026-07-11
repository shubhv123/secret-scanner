# Secret Scanner

`secret-scanner` is a high-performance, zero-dependency, open-source security tool built in Python. It detects accidentally exposed credentials, private keys, passwords, and sensitive API tokens in files, local Git history, and remote GitHub repositories. 

It integrates seamlessly with Git as a **pre-commit hook** to block commits containing secrets, protecting your codebase prior to any push.

---

## Key Features

- **Multi-layered Detection**:
  - **Signature Matching**: Pre-compiled regex patterns for popular services (AWS, GitHub, Slack, Stripe, Google Cloud, private keys, database connections).
  - **Dynamic Shannon Entropy**: Shannon entropy calculations identify high-entropy random keys and custom passwords.
- **Git Hooks**: Native Git pre-commit integration scanning only staged lines (`git diff -U0`) to block leaks without introducing legacy codebase warnings.
- **Remote Scanning**: Clone and scan remote public/private GitHub repositories directly from a URL.
- **Fast Execution**: Parallelized file-system traversal utilizing multi-threading.
- **Customizable**: Set rules, keywords, ignore files, and directories in a clean TOML configuration file.
- **Obfuscation**: Automatically hides raw secret values in CLI, Markdown, and JSON output (e.g. `AKIA************ABCD`) for security.
- **Bypass Command**: False positives can be bypassed inline using `# secret-scanner:ignore`.

---

## Directory Structure

```
secret_scanner/
├── secret_scanner/
│   ├── __init__.py
│   ├── cli.py             # CLI parser and execution router
│   ├── scanner.py         # File, directory, and Git log scanning logic
│   ├── github_scanner.py  # Clones and scans remote GitHub repositories
│   ├── rules.py           # Regex patterns, entropy calculations, bypass logic
│   ├── hooks.py           # Pre-commit hook installation and staged diff analysis
│   └── formatter.py       # Console, JSON, and Markdown format output
├── config.toml            # Global rules and scanning configuration
├── setup.py               # Package setup script
├── README.md              # Documentation
└── tests/                 # Unit tests
    ├── __init__.py
    ├── test_scanner.py
    └── test_rules.py
```

---

## Installation

Verify that you are using Python 3.11+ (which includes native `tomllib` support).

1. Clone or download this repository.
2. From the root directory of the tool, run:
   ```bash
   pip install -e .
   ```
This installs the tool in editable development mode and makes the `secret-scanner` command available globally in your terminal.

---

## Usage

### 1. Scanning a Local File or Directory
To scan files or directory trees (it automatically excludes folders like `node_modules`, `.git`, `venv` etc.):
```bash
# Scan current directory
secret-scanner scan

# Scan specific folder or file
secret-scanner scan /path/to/project
```

### 2. Scanning Git History
To scan every commit in the repository's git logs and identify when and where keys were added:
```bash
secret-scanner scan --git-history
```

### 3. Scanning a Remote GitHub Repository
To temporarily clone and scan a remote GitHub repository:
```bash
# Public repository snapshot
secret-scanner clone-scan https://github.com/user/repo.git

# Scanning remote repository including full git history
secret-scanner clone-scan https://github.com/user/repo.git --git-history

# Authenticating for private repositories using a GitHub token
secret-scanner clone-scan https://github.com/user/repo.git --token YOUR_GITHUB_TOKEN
```

### 4. Git Pre-Commit Hook Integration
Prevent commits with secrets from ever reaching your Git repository:

```bash
# Install hook in current repository
secret-scanner install-hook

# Uninstall hook
secret-scanner uninstall-hook
```
When installed, running `git commit` automatically triggers a staged-changes-only scan. If a leak is found, the commit is blocked and a warning table is output.

---

## Configuration (`config.toml`)

The tool checks for a `config.toml` or `.secret-scanner.toml` in your project folder, falling back to its internal configuration if not found. You can configure:
- **`[entropy]`**: Configure the baseline entropy `threshold` (default: `4.5`), `min_length` of credentials, and generic keywords (like `key`, `secret`, `password`) that trigger searches.
- **`[ignore]`**: Exclude specific directories, filenames, or file extensions from traversal scans.
- **`[[rules]]`**: Add your own regex patterns to look for custom internal secret structures.

Example rule addition:
```toml
[[rules]]
name = "My Custom App Token"
pattern = '\bmy_app_[0-9a-f]{32}\b'
description = "Detected My Custom App API Token."
```

---

## Ignoring False Positives

If a line flags a false positive (such as a public test credential), you can exclude it by adding an inline comment:

```javascript
const apiKey = "AKIA1234567890ABCDEF"; // secret-scanner:ignore
```
Any line containing `secret-scanner:ignore` will bypass rules checks and be skipped.

---

## Output Formats

Support outputting results in multiple formats using the `--format` option:
- **Console (default)**: Colorized, human-readable terminal table.
- **JSON**: Structured JSON output (with obfuscated fields) suitable for integration into CI/CD pipelines (GitHub Actions, GitLab CI, etc.).
- **Markdown**: Formatted markdown report suitable for posting as commit comments or issues.

```bash
secret-scanner scan --format json
secret-scanner scan --format markdown
```

---

## Running Tests
Run the unit test suite:
```bash
python3 -m unittest discover -s tests
```
