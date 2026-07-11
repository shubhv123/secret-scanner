import json
from typing import Dict, Any, List

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

def obfuscate_secret(secret: str) -> str:
    """Obfuscates a secret to prevent exposing it in reports."""
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    # Keep first 4 and last 4 characters, obfuscating the middle
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"

def format_console(findings: List[Dict[str, Any]]) -> str:
    """Formats findings into a beautiful, colorized terminal table."""
    if not findings:
        return f"{GREEN}{BOLD}✔ No secrets or sensitive keys detected.{RESET}"

    lines = []
    lines.append(f"{RED}{BOLD}✗ Found {len(findings)} potential secret leak(s):{RESET}\n")

    # Determine if this includes git history findings
    is_git_history = any("commit" in f for f in findings)

    if is_git_history:
        # Commit, File, Line, Rule, Secret
        header_format = f"{BOLD}{CYAN}{'Commit':<10} {'File':<25} {'Line':<6} {'Rule':<30} {'Secret (Obfuscated)':<20}{RESET}"
        lines.append(header_format)
        lines.append("-" * 95)
        for f in findings:
            commit = f.get("commit", "N/A")[:8]
            file_path = f.get("file", "unknown")
            if len(file_path) > 24:
                file_path = "..." + file_path[-21:]
            line_no = str(f.get("line_no", 0))
            rule = f.get("rule", "Unknown")
            if len(rule) > 29:
                rule = rule[:26] + "..."
            obfuscated = obfuscate_secret(f.get("secret", ""))
            
            lines.append(f"{YELLOW}{commit:<10}{RESET} {file_path:<25} {line_no:<6} {RED}{rule:<30}{RESET} {obfuscated:<20}")
    else:
        # File, Line, Rule, Secret, Context
        header_format = f"{BOLD}{CYAN}{'File':<35} {'Line':<6} {'Rule':<30} {'Secret (Obfuscated)':<20}{RESET}"
        lines.append(header_format)
        lines.append("-" * 95)
        for f in findings:
            file_path = f.get("file", "unknown")
            if len(file_path) > 34:
                file_path = "..." + file_path[-31:]
            line_no = str(f.get("line_no", 0))
            rule = f.get("rule", "Unknown")
            if len(rule) > 29:
                rule = rule[:26] + "..."
            obfuscated = obfuscate_secret(f.get("secret", ""))
            
            lines.append(f"{file_path:<35} {line_no:<6} {RED}{rule:<30}{RESET} {obfuscated:<20}")

    lines.append("")
    lines.append(f"{RED}{BOLD}Action Required: Remove these secrets before pushing to any remote repository!{RESET}")
    lines.append(f"{YELLOW}Tip: Use '# secret-scanner:ignore' inline to bypass warning on a specific line.{RESET}")
    return "\n".join(lines)

def format_json(findings: List[Dict[str, Any]]) -> str:
    """Formats findings into a structured JSON string."""
    # Create a copy and obfuscate secrets in the JSON output for safety
    safe_findings = []
    for f in findings:
        f_copy = f.copy()
        f_copy["secret_obfuscated"] = obfuscate_secret(f.get("secret", ""))
        safe_findings.append(f_copy)
    return json.dumps(safe_findings, indent=2)

def format_markdown(findings: List[Dict[str, Any]]) -> str:
    """Formats findings into a Markdown report."""
    if not findings:
        return "## ✔ Secret Scanner Report\n\nNo secrets detected."

    lines = []
    lines.append("## ✗ Secret Scanner Report")
    lines.append(f"Found {len(findings)} potential secret leaks in the codebase.\n")

    is_git_history = any("commit" in f for f in findings)

    if is_git_history:
        lines.append("| Commit | File | Line | Rule | Secret (Obfuscated) | Description |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for f in findings:
            commit = f.get("commit", "N/A")[:8]
            file_path = f.get("file", "unknown")
            line_no = f.get("line_no", 0)
            rule = f.get("rule", "Unknown")
            obfuscated = obfuscate_secret(f.get("secret", ""))
            desc = f.get("description", "")
            lines.append(f"| `{commit}` | `{file_path}` | {line_no} | **{rule}** | `{obfuscated}` | {desc} |")
    else:
        lines.append("| File | Line | Rule | Secret (Obfuscated) | Description |")
        lines.append("| --- | --- | --- | --- | --- |")
        for f in findings:
            file_path = f.get("file", "unknown")
            line_no = f.get("line_no", 0)
            rule = f.get("rule", "Unknown")
            obfuscated = obfuscate_secret(f.get("secret", ""))
            desc = f.get("description", "")
            lines.append(f"| `{file_path}` | {line_no} | **{rule}** | `{obfuscated}` | {desc} |")

    lines.append("\n> [!WARNING]\n> Please rotate any leaked credentials and remove them from repository history.")
    return "\n".join(lines)
