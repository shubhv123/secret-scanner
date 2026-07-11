from setuptools import setup, find_packages

setup(
    name="secret-scanner",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "secret-scanner=secret_scanner.cli:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.11",
    author="Antigravity",
    description="A dependency-free CLI tool to scan codebases and GitHub repos for secrets, with Git pre-commit hooks.",
)
