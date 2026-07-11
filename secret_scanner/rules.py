import math
import re
import os
from collections import Counter
from typing import Dict, Any, List, Optional, Tuple

# Built-in fallback config if no config file is loaded
DEFAULT_CONFIG = {
    "entropy": {
        "threshold": 4.5,
        "min_length": 16,
        "keywords": ["key", "secret", "token", "password", "pwd", "auth", "credential", "private", "access"]
    },
    "ignore": {
        "directories": ["node_modules", ".git", "venv", "env", ".venv", "__pycache__", ".pytest_cache", "build", "dist"],
        "files": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Gemfile.lock", "Cargo.lock"],
        "extensions": ["png", "jpg", "jpeg", "gif", "ico", "svg", "webp", "mp4", "mp3", "pdf", "zip", "tar", "gz", "pyc", "db"]
    },
    "rules": [
        {
            "name": "AWS Access Key ID",
            "pattern": r'\b(?:AKIA|ASCA|AGPA|AIDA)[0-9A-Z]{16}\b',
            "description": "Detected AWS Access Key ID, which exposes access to AWS accounts."
        },
        {
            "name": "AWS Secret Access Key",
            "pattern": r'(?i)(?:aws_secret|aws_secret_access_key|aws_key)\s*[:=]\s*["\']([A-Za-z0-9/+=]{40})["\']',
            "description": "Detected potential AWS Secret Access Key."
        },
        {
            "name": "GitHub Personal Access Token (Classic)",
            "pattern": r'\bghp_[a-zA-Z0-9]{36}\b',
            "description": "Detected GitHub Personal Access Token (Classic)."
        },
        {
            "name": "GitHub Fine-Grained Token",
            "pattern": r'\bgithub_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}\b',
            "description": "Detected GitHub Fine-Grained Personal Access Token."
        },
        {
            "name": "Slack Bot Token",
            "pattern": r'\bxoxb-[0-9a-zA-Z]{10,48}\b',
            "description": "Detected Slack Bot Token."
        },
        {
            "name": "Slack User Token",
            "pattern": r'\bxoxp-[0-9a-zA-Z]{10,48}\b',
            "description": "Detected Slack User Token."
        },
        {
            "name": "Slack Webhook",
            "pattern": r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,11}/B[a-zA-Z0-9_]{8,11}/[a-zA-Z0-9_]{24}',
            "description": "Detected Slack Webhook URL, allowing raw message posts."
        },
        {
            "name": "Stripe Publishable Key",
            "pattern": r'\bpk_(?:live|test)_[0-9a-zA-Z]{24,34}\b',
            "description": "Detected Stripe Publishable API Key."
        },
        {
            "name": "Stripe Secret Key",
            "pattern": r'\bsk_(?:live|test)_[0-9a-zA-Z]{24,34}\b',
            "description": "Detected Stripe Secret API Key (exposes account operations)."
        },
        {
            "name": "Google API Key",
            "pattern": r'\bAIza[0-9A-Za-z-_]{35}\b',
            "description": "Detected Google API Key, exposing access to GCP APIs."
        },
        {
            "name": "Generic Private Key",
            "pattern": r'-----BEGIN (?:RSA|EC|PGP|OPENSSH|DSA)? PRIVATE KEY-----',
            "description": "Detected asymmetric Private Key, which controls identity/auth for servers or services."
        },
        {
            "name": "Database Connection String",
            "pattern": r'\b(?:postgres(?:ql)?|mongodb(?:\+srv)?|redis|mysql|mssql|oracle):\/\/[^:]+:[^@]+@[^/\s]+',
            "description": "Detected potential Database Connection URL with inline username and password."
        }
    ]
}


def calculate_entropy(text: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    counts = Counter(text)
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


class RuleMatcher:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.compiled_rules = self._compile_rules()
        self.entropy_regex = self._compile_entropy_regex()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Loads configuration from TOML file, falling back to DEFAULT_CONFIG."""
        config = DEFAULT_CONFIG.copy()
        
        # Check standard config locations if config_path is not specified
        search_paths = []
        if config_path:
            search_paths.append(config_path)
        else:
            search_paths.extend([
                os.path.join(os.getcwd(), ".secret-scanner.toml"),
                os.path.join(os.getcwd(), "config.toml"),
                # Fallback to config next to setup.py if workspace config exists
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.toml")
            ])

        loaded = False
        for path in search_paths:
            if os.path.exists(path):
                try:
                    import tomllib
                    with open(path, "rb") as f:
                        toml_data = tomllib.load(f)
                        # Merge configuration keys safely
                        if "entropy" in toml_data:
                            config["entropy"].update(toml_data["entropy"])
                        if "ignore" in toml_data:
                            config["ignore"].update(toml_data["ignore"])
                        if "rules" in toml_data:
                            config["rules"] = toml_data["rules"]
                        loaded = True
                        break
                except Exception as e:
                    # Log silently or ignore, falling back to default
                    pass

        return config

    def _compile_rules(self) -> List[Tuple[str, re.Pattern, str]]:
        """Compiles rule regular expressions."""
        compiled = []
        for rule in self.config.get("rules", []):
            name = rule.get("name", "Unknown Rule")
            pattern = rule.get("pattern", "")
            desc = rule.get("description", "")
            if pattern:
                try:
                    compiled.append((name, re.compile(pattern), desc))
                except re.error:
                    # Ignore invalid regex patterns
                    pass
        return compiled

    def _compile_entropy_regex(self) -> re.Pattern:
        """
        Compiles the regex pattern for finding variable assignments with high entropy string candidates.
        Matches: key_name = "value" or "key_name": 'value'
        """
        keywords = self.config.get("entropy", {}).get("keywords", DEFAULT_CONFIG["entropy"]["keywords"])
        kw_pattern = "|".join(re.escape(kw) for kw in keywords)
        
        # Look for assignment: keyword optionally preceded/followed by identifier chars
        # then : or = then a quoted string containing alphanumeric/symbol characters
        pattern_str = rf'(?i)\b[A-Za-z0-9_-]*(?:{kw_pattern})[A-Za-z0-9_-]*\s*[:=]\s*["\']([A-Za-z0-9/+=_\-@#%^&*!]{{8,}})["\']'
        return re.compile(pattern_str)

    def is_ignored_file(self, file_path: str) -> bool:
        """Determines if a file path matches ignore lists (directories, names, extensions)."""
        parts = os.path.split(file_path)
        filename = parts[-1]
        
        # Skip empty filename/paths
        if not filename:
            return True

        # Check directories in path
        path_parts = re.split(r'[\\/]', file_path)
        for ignored_dir in self.config.get("ignore", {}).get("directories", []):
            if ignored_dir in path_parts:
                return True

        # Check file name
        if filename in self.config.get("ignore", {}).get("files", []):
            return True

        # Check extensions
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext in self.config.get("ignore", {}).get("extensions", []):
            return True

        return False

    def scan_line(self, line: str, line_no: int = 1) -> List[Dict[str, Any]]:
        """Scans a line for leaks. Returns a list of findings."""
        findings = []

        # Check if line contains inline exclusion comment
        if "secret-scanner:ignore" in line:
            return findings

        # 1. Check regex rules
        for name, pattern, desc in self.compiled_rules:
            matches = pattern.findall(line)
            for m in matches:
                # If group matches, get the actual secret part
                secret = m[0] if isinstance(m, tuple) else m
                if "secret-scanner:ignore" in line or not secret:
                    continue
                
                # Check for common dummy strings
                if self._is_dummy(secret):
                    continue

                findings.append({
                    "rule": name,
                    "secret": secret,
                    "description": desc,
                    "line_no": line_no
                })

        # 2. Check general high entropy strings assigned to credentials
        entropy_matches = self.entropy_regex.findall(line)
        min_len = self.config.get("entropy", {}).get("min_length", 16)
        threshold = self.config.get("entropy", {}).get("threshold", 4.5)

        for value in entropy_matches:
            # Clean quotes if any
            clean_value = value.strip('"\'')
            if len(clean_value) >= min_len:
                # Exclude if matched a regex rule already (avoid duplicate findings)
                if any(f["secret"] in clean_value or clean_value in f["secret"] for f in findings):
                    continue

                # Exclude dummy strings
                if self._is_dummy(clean_value):
                    continue

                is_hex = all(c in "0123456789abcdefABCDEF" for c in clean_value)
                # Hex strings have max entropy of 4.0, so lower the threshold for them
                effective_threshold = 3.0 if (is_hex and threshold > 3.0) else threshold
                
                entropy = calculate_entropy(clean_value)
                if entropy >= effective_threshold:
                    findings.append({
                        "rule": "High Entropy Credential",
                        "secret": clean_value,
                        "description": f"Potential high entropy key/secret detected (Entropy: {entropy:.2f}).",
                        "line_no": line_no
                    })

        return findings

    def _is_dummy(self, text: str) -> bool:
        """Checks if a string is a placeholder/dummy value like 'your_key_here'."""
        dummy_words = [
            "your_key", "my_key", "placeholder", "dummy", "example", 
            "insert_here", "todo", "replace_me", "test_key", "secret_key"
        ]
        text_lower = text.lower()
        return any(w in text_lower for w in dummy_words) or len(set(text)) <= 3
