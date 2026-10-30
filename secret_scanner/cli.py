import argparse
import sys
import os
from secret_scanner.rules import RuleMatcher
from secret_scanner.scanner import Scanner
from secret_scanner.github_scanner import GitHubScanner
from secret_scanner.hooks import HookManager
from secret_scanner import formatter

def main(args_list=None):
    parser = argparse.ArgumentParser(
        description="Secret Scanner: Find accidentally exposed passwords, keys, and tokens in codebases and Git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument("--config", help="Path to custom TOML configuration file.")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format (default: text).")
    parser.add_argument("--entropy-threshold", type=float, help="Override the Shannon entropy threshold (e.g. 4.5).")

    subparsers = parser.add_subparsers(dest="command", help="Scanner commands")

    # Command: scan
    scan_parser = subparsers.add_parser("scan", help="Scan a local file, directory, or staged changes.")
    scan_parser.add_argument("path", nargs="?", default=".", help="Path to scan (file or directory, defaults to '.').")
    scan_parser.add_argument("--pre-commit", action="store_true", help="Run as a git pre-commit hook scanning only staged changes.")
    scan_parser.add_argument("--git-history", action="store_true", help="Scan the full git commit history of the local repository.")

    # Command: clone-scan
    clone_parser = subparsers.add_parser("clone-scan", help="Clone and scan a remote GitHub repository.")
    clone_parser.add_argument("url", help="GitHub repository URL (HTTPS or SSH).")
    clone_parser.add_argument("--token", help="GitHub Personal Access Token for private repositories.")
    clone_parser.add_argument("--git-history", action="store_true", help="Scan full git history of the remote repository.")

    # Command: install-hook
    subparsers.add_parser("install-hook", help="Install the Git pre-commit hook in the current repository.")

    # Command: uninstall-hook
    subparsers.add_parser("uninstall-hook", help="Uninstall the Git pre-commit hook from the current repository.")

    # Parse arguments
    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        return 0

    try:
        # Initialize components
        rule_matcher = RuleMatcher(config_path=args.config)
        
        # Override entropy threshold if passed via CLI
        if args.entropy_threshold is not None:
            rule_matcher.config["entropy"]["threshold"] = args.entropy_threshold

        scanner = Scanner(rule_matcher)
        github_scanner = GitHubScanner(scanner)
        hook_manager = HookManager(os.getcwd())

        findings = []

        # Route commands
        if args.command == "scan":
            if args.pre_commit:
                # Pre-commit hook mode: scan staged changes only
                findings = hook_manager.scan_staged_changes(rule_matcher)
            elif args.git_history:
                # Scan git logs and diffs
                findings = scanner.scan_git_history(args.path)
            else:
                # Scan normal files
                target_path = os.path.abspath(args.path)
                if os.path.isdir(target_path):
                    findings = scanner.scan_directory(target_path)
                else:
                    findings = scanner.scan_file(target_path)

        elif args.command == "clone-scan":
            findings = github_scanner.scan_remote_repo(
                repo_url=args.url,
                token=args.token,
                scan_history=args.git_history
            )

        elif args.command == "install-hook":
            hook_manager.install()
            print(f"{formatter.GREEN}{formatter.BOLD}✔ Pre-commit hook successfully installed at .git/hooks/pre-commit{formatter.RESET}")
            return 0

        elif args.command == "uninstall-hook":
            if hook_manager.uninstall():
                print(f"{formatter.GREEN}✔ Pre-commit hook successfully uninstalled.{formatter.RESET}")
            else:
                print(f"{formatter.YELLOW}No pre-commit hook installed by secret-scanner was found.{formatter.RESET}")
            return 0

        # Output formatting
        if args.format == "json":
            print(formatter.format_json(findings))
        elif args.format == "markdown":
            print(formatter.format_markdown(findings))
        else:
            print(formatter.format_console(findings))

        # Exit code: 1 if secrets found (important for git hooks), 0 if clean
        return 1 if findings else 0

    except Exception as e:
        print(f"{formatter.RED}{formatter.BOLD}Error: {str(e)}{formatter.RESET}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
