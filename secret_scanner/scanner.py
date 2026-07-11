import os
import re
import subprocess
import concurrent.futures
from typing import Dict, Any, List, Optional
from secret_scanner.rules import RuleMatcher

class Scanner:
    def __init__(self, rule_matcher: RuleMatcher, num_threads: int = 4):
        self.matcher = rule_matcher
        self.num_threads = num_threads

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scans a single file line by line for secrets."""
        findings = []
        if self.matcher.is_ignored_file(file_path):
            return findings

        if not os.path.isfile(file_path):
            return findings

        # Safely open file, falling back to different encodings if needed
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    # Strip newline for matching
                    clean_line = line.rstrip("\n")
                    line_findings = self.matcher.scan_line(clean_line, line_no)
                    for f_item in line_findings:
                        findings.append({
                            "file": file_path,
                            "line_no": f_item["line_no"],
                            "rule": f_item["rule"],
                            "secret": f_item["secret"],
                            "description": f_item["description"],
                            "line_content": clean_line.strip()
                        })
        except Exception as e:
            # Skip files that can't be read (e.g. permission error, locked files)
            pass

        return findings

    def scan_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """Scans a directory recursively using thread pool executor."""
        all_findings = []
        file_paths = []

        for root, dirs, files in os.walk(dir_path):
            # Prune ignored directories in-place to optimize traversal
            dirs[:] = [d for d in dirs if not self.matcher.is_ignored_file(os.path.join(root, d))]

            for file in files:
                full_path = os.path.join(root, file)
                if not self.matcher.is_ignored_file(full_path):
                    file_paths.append(full_path)

        # Scan files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_file = {executor.submit(self.scan_file, fp): fp for fp in file_paths}
            for future in concurrent.futures.as_completed(future_to_file):
                file_findings = future.result()
                if file_findings:
                    all_findings.extend(file_findings)

        return all_findings

    def scan_git_history(self, repo_path: str) -> List[Dict[str, Any]]:
        """
        Scans full Git commit logs and diffs for secrets.
        Runs 'git log -p' and parses the stream.
        """
        findings = []
        if not os.path.exists(os.path.join(repo_path, ".git")):
            return findings

        try:
            # Run git log -p to get commits and diffs
            cmd = ["git", "log", "-p", "--all", "--full-history"]
            process = subprocess.Popen(
                cmd,
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            
            current_commit = None
            current_author = None
            current_date = None
            current_file = None
            line_no = 0

            # Stream stdout line by line to minimize memory usage
            for line in process.stdout:
                line = line.rstrip("\n")

                if line.startswith("commit "):
                    current_commit = line.split(" ")[1]
                    current_file = None
                    line_no = 0
                elif line.startswith("Author: ") and current_commit:
                    current_author = line[8:]
                elif line.startswith("Date: ") and current_commit:
                    current_date = line[6:]
                elif line.startswith("diff --git ") and current_commit:
                    # Reset line counter for new file diff
                    line_no = 0
                    current_file = None
                elif line.startswith("+++ b/") and current_commit:
                    current_file = line[6:]
                    line_no = 0
                elif line.startswith("@@ ") and current_commit:
                    # Parse hunk header for line numbers (e.g. @@ -12,4 +12,6 @@)
                    # We can estimate line numbers for addition: +12,6 means additions start at line 12
                    match = re.search(r'\+(\d+)', line)
                    if match:
                        line_no = int(match.group(1)) - 1 # We increment prior to matching
                elif line.startswith("+") and not line.startswith("+++") and current_commit and current_file:
                    line_no += 1
                    # Skip files that match ignore rules
                    if self.matcher.is_ignored_file(current_file):
                        continue

                    added_line = line[1:] # strip the '+' sign
                    line_findings = self.matcher.scan_line(added_line, line_no)
                    for f_item in line_findings:
                        findings.append({
                            "commit": current_commit,
                            "author": current_author,
                            "date": current_date,
                            "file": current_file,
                            "line_no": f_item["line_no"],
                            "rule": f_item["rule"],
                            "secret": f_item["secret"],
                            "description": f_item["description"],
                            "line_content": added_line.strip()
                        })
                elif line.startswith(" ") and not line.startswith("---") and current_commit and current_file:
                    # Unmodified line in diff, still keep track of line counter
                    line_no += 1

            process.wait()
        except Exception as e:
            # Handle Git errors silently or return what we have
            pass

        return findings
