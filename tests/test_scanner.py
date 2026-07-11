import unittest
import tempfile
import os
from secret_scanner.rules import RuleMatcher
from secret_scanner.scanner import Scanner

class TestScanner(unittest.TestCase):
    def setUp(self):
        self.matcher = RuleMatcher()
        self.scanner = Scanner(self.matcher)

    def test_scan_file_with_secret(self):
        # Create a temp file with a secret
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".py") as f:
            f.write("# Some python file\n")
            f.write("aws_secret = 'AKIA1234567890ABCDEF'\n")  # Should be flagged by AWS key regex
            f_path = f.name

        try:
            findings = self.scanner.scan_file(f_path)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["rule"], "AWS Access Key ID")
            self.assertEqual(findings[0]["file"], f_path)
        finally:
            os.remove(f_path)

    def test_scan_file_no_secret(self):
        # Create a temp file with clean content
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".py") as f:
            f.write("# Clean file\n")
            f.write("print('Hello World')\n")
            f_path = f.name

        try:
            findings = self.scanner.scan_file(f_path)
            self.assertEqual(len(findings), 0)
        finally:
            os.remove(f_path)

    def test_scan_directory(self):
        # Create a temp directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # File 1: in root, has secret
            f1_path = os.path.join(temp_dir, "app.py")
            with open(f1_path, "w") as f:
                f.write("github_token = 'ghp_123456789012345678901234567890123456'\n")

            # File 2: in root, clean
            f2_path = os.path.join(temp_dir, "README.md")
            with open(f2_path, "w") as f:
                f.write("# README\nNo keys here.")

            # File 3: in ignored directory, has secret (should be ignored)
            node_modules_dir = os.path.join(temp_dir, "node_modules")
            os.makedirs(node_modules_dir)
            f3_path = os.path.join(node_modules_dir, "package.js")
            with open(f3_path, "w") as f:
                f.write("secret = 'AKIA1234567890ABCDEF'\n")

            # File 4: ignored file name, has secret (should be ignored)
            f4_path = os.path.join(temp_dir, "package-lock.json")
            with open(f4_path, "w") as f:
                f.write("secret = 'AKIA1234567890ABCDEF'\n")

            # File 5: ignored extension, has secret (should be ignored)
            f5_path = os.path.join(temp_dir, "image.png")
            with open(f5_path, "w") as f:
                f.write("secret = 'AKIA1234567890ABCDEF'\n")

            findings = self.scanner.scan_directory(temp_dir)
            
            # Should only find the secret in app.py (File 1)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["file"], f1_path)
            self.assertEqual(findings[0]["rule"], "GitHub Personal Access Token (Classic)")

if __name__ == '__main__':
    unittest.main()
