# CLAUDE.md — Repository Context & Migration Guardrails

## Active Dependency Standards
- **setuptools**: `84.2.1` (Upgraded from `legacy` via DriftZero)
- **Verification Suite**: `pytest test_migration_parity.py -v`

## Strict Coding Rules for AI Agents
### setup() license argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', license='MIT')`
- **REQUIRED (Target 84.2.1):** `setup(name='myproj', version='1.0', license_files=['LICENSE'])`
- **Required Imports:** `from setuptools import setup`
- **Silent Semantic Drift Warning:** The license argument only accepted a string; license_files expects a list of file paths or globs, and is used for metadata.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### setup() provides argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', provides=['mymodule'])`
- **REQUIRED (Target 84.2.1):** `setup(name='myproj', version='1.0')`
- **Required Imports:** ``
- **Silent Semantic Drift Warning:** Provides was ignored by modern installers; removing avoids warnings.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### setup() requires argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', requires=['requests>=2.0'])`
- **REQUIRED (Target 84.2.1):** `setup(name='myproj', version='1.0', install_requires=['requests>=2.0'])`
- **Required Imports:** ``
- **Silent Semantic Drift Warning:** requires was deprecated; install_requires is the correct field for runtime dependencies.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### setup() obsoletes argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', obsoletes=['oldpkg'])`
- **REQUIRED (Target 84.2.1):** `# obsoletes removed; use conflict handling via other tools if needed`
- **Required Imports:** ``
- **Silent Semantic Drift Warning:** Obsoletes is no longer supported; cannot express package obsolescence in metadata.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### setup() namespace_packages argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', namespace_packages=['myns'])`
- **REQUIRED (Target 84.2.1):** `from setuptools import find_namespace_packages
setup(name='myproj', version='1.0', packages=find_namespace_packages())`
- **Required Imports:** `from setuptools import find_namespace_packages`
- **Silent Semantic Drift Warning:** namespace_packages is deprecated; find_namespace_packages automatically discovers namespace packages.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### setup() setup_requires argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', setup_requires=['wheel'])`
- **REQUIRED (Target 84.2.1):** `# Move build dependencies to pyproject.toml
[build-system]
requires = ['setuptools>=61.0', 'wheel']
build-backend = 'setuptools.build_meta'`
- **Required Imports:** ``
- **Silent Semantic Drift Warning:** setup_requires is ignored with PEP 517 builds; declare build-system in pyproject.toml.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### setup() tests_require argument
- **FORBIDDEN (Legacy legacy):** `setup(name='myproj', version='1.0', tests_require=['pytest'])`
- **REQUIRED (Target 84.2.1):** `# Define test dependencies in pyproject.toml under [project] optional-dependencies.test or CI config`
- **Required Imports:** ``
- **Silent Semantic Drift Warning:** tests_require is deprecated; use project.optional-dependencies.test or CI configuration.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html

### find_packages() with implicit root
- **FORBIDDEN (Legacy legacy):** `packages=find_packages()`
- **REQUIRED (Target 84.2.1):** `packages=find_packages(where='src')`
- **Required Imports:** `from setuptools import find_packages`
- **Silent Semantic Drift Warning:** When source code lives inside a src/ layout, explicitly set where='src' to avoid picking up unwanted directories.
- **Verified Source:** https://setuptools.pypa.io/en/stable/history.html


## Sandbox Quality Assurance
- Autonomous self-healing patched `secret_scanner/hooks.py, secret_scanner/scanner.py` to eliminate silent semantic drift. Always verify default arguments, validation lifecycles, and keyword arguments in setuptools 84.2.1.
- Autonomous self-healing patched `secret_scanner/scanner.py, secret_scanner/cli.py` to eliminate silent semantic drift. Always verify default arguments, validation lifecycles, and keyword arguments in setuptools 84.2.1.
