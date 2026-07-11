import os
import subprocess
import tempfile
import urllib.parse
from typing import Dict, Any, List, Optional
from secret_scanner.scanner import Scanner

class GitHubScanner:
    def __init__(self, scanner: Scanner):
        self.scanner = scanner

    def _prepare_clone_url(self, repo_url: str, token: Optional[str] = None) -> str:
        """Injects GitHub auth token into repo URL if provided."""
        if not token:
            return repo_url

        # Handle HTTPS URL
        if repo_url.startswith("https://"):
            parsed = urllib.parse.urlparse(repo_url)
            # Format: https://<token>@github.com/owner/repo.git
            netloc = f"{token}@{parsed.netloc}"
            return urllib.parse.urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        
        # If it's already an SSH URL, return as-is (auth is handled by SSH key)
        return repo_url

    def scan_remote_repo(self, repo_url: str, token: Optional[str] = None, scan_history: bool = False) -> List[Dict[str, Any]]:
        """Clones a remote GitHub repository into a temp directory and scans it."""
        findings = []
        clone_url = self._prepare_clone_url(repo_url, token)

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone the repo into the temp directory
                # Use --depth=1 if we don't need history, which is much faster!
                clone_cmd = ["git", "clone"]
                if not scan_history:
                    clone_cmd.extend(["--depth", "1"])
                
                clone_cmd.extend([clone_url, temp_dir])

                # Suppress output of git clone to make the CLI output clean
                result = subprocess.run(
                    clone_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

                # Scan the temp directory
                if scan_history:
                    raw_findings = self.scanner.scan_git_history(temp_dir)
                else:
                    raw_findings = self.scanner.scan_directory(temp_dir)

                # Convert findings' file paths to be relative to the repo root
                for f in raw_findings:
                    # Make path relative to temp_dir
                    rel_path = os.path.relpath(f["file"], temp_dir)
                    f["file"] = rel_path
                    findings.append(f)

            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to clone GitHub repository: {repo_url}. Check if the repository exists or if credentials are correct.")
            except Exception as e:
                raise RuntimeError(f"An error occurred during GitHub scanning: {str(e)}")

        return findings
