# CI/CD Process Guide - Startup Intelligence Analysis App

## 🎯 Quick Start - Understanding Your CI/CD

### 1. View CI/CD Status (Multiple Ways)

#### A. Via GitHub Web Interface
```bash
# Open your browser to:
https://github.com/shankerram3/Startup-Intelligence-Analysis-App/actions

# Or for a specific branch:
https://github.com/shankerram3/Startup-Intelligence-Analysis-App/actions?query=branch%3Aclaude%2Freview-main-branch-01PB9bDdkMjtqBzv7sULEoU9
```

#### B. Via GitHub CLI (gh)
```bash
# Install gh if not available
# brew install gh  # macOS
# apt install gh   # Linux

# View recent workflow runs
gh run list --limit 10

# View specific workflow run
gh run view

# Watch a workflow run in real-time
gh run watch

# View logs for failed jobs
gh run view --log-failed
```

#### C. Via Git Commit Status
```bash
# Check commit status locally
git log --oneline --decorate -1

# View commit status with details
gh api repos/shankerram3/Startup-Intelligence-Analysis-App/commits/$(git rev-parse HEAD)/status
```

---

## 📋 Your Current CI/CD Pipeline

### Pipeline Overview (From `.github/workflows/ci.yml`)

```
┌─────────────────────────────────────────────────────────────┐
│                    PUSH TO BRANCH                            │
│         (main, develop, claude/*)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌─────────────┐
│ Code Quality │ │ Security │ │ Unit Tests  │
│              │ │          │ │             │
│ - Black      │ │ - Bandit │ │ - pytest    │
│ - isort      │ │ - Safety │ │ - coverage  │
│ - pylint     │ │ - Secrets│ │ - codecov   │
│ - mypy       │ │          │ │             │
└──────┬───────┘ └────┬─────┘ └──────┬──────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌────────────┐ ┌──────────────┐
│Integration  │ │Docker Build│ │Dependencies  │
│   Tests     │ │            │ │   Audit      │
│             │ │ - Build    │ │              │
│ - Neo4j     │ │ - Test     │ │ - Outdated   │
│ - Redis     │ │            │ │ - Verify     │
└──────┬──────┘ └─────┬──────┘ └──────┬───────┘
       │              │               │
       └──────────────┼───────────────┘
                      │
                      ▼
              ┌──────────────┐
              │  CI Success  │
              │   (Summary)  │
              └──────────────┘
```

---

## 🔍 Understanding Each CI/CD Job

### Job 1: Code Quality (code-quality)
**What it does:** Ensures code follows style guidelines

```bash
# Runs these checks:
1. black --check .              # Code formatting
2. isort --check .              # Import sorting
3. pylint api.py ...            # Code linting
4. mypy api.py ...              # Type checking

# Current Status: ⚠️ LENIENT
# - pylint: || true (failures allowed)
# - mypy: || true (failures allowed)
```

**How to run locally:**
```bash
# Run all quality checks
make lint
make format-check
make type-check

# Or manually:
black --check .
isort --check .
pylint api.py pipeline.py
mypy api.py --ignore-missing-imports
```

**Common Issues:**
- Formatting errors → Run `make format` to auto-fix
- Import ordering → Run `isort .` to fix
- Type errors → Currently ignored with `|| true`

---

### Job 2: Security Scan (security)
**What it does:** Scans for security vulnerabilities

```bash
# Runs these checks:
1. bandit -r .                  # Security scan
2. pip-audit                    # Dependency vulnerabilities
3. grep for hardcoded secrets   # API key detection

# Current Status: ⚠️ LENIENT
# - bandit: || true (failures allowed)
# - pip-audit: || true (failures allowed)
```

**How to run locally:**
```bash
# Run security checks
make security-check

# Or manually:
pip install bandit pip-audit
bandit -r . -ll -i -x tests/,frontend/,venv/
pip-audit
grep -r "sk-[a-zA-Z0-9]" --include="*.py" .
```

**Common Issues:**
- Bandit warnings → Review and fix or add # nosec comment
- Vulnerable packages → Update with pip install --upgrade
- Hardcoded secrets → Move to environment variables

---

### Job 3: Unit Tests (test-unit)
**What it does:** Runs fast, isolated tests

```bash
# Runs:
pytest tests/unit -v
pytest tests/unit --cov=. --cov-report=xml

# Coverage uploaded to: codecov.io
```

**How to run locally:**
```bash
# Run unit tests
make test-unit

# With coverage
make test-coverage

# Watch mode (requires pytest-watch)
make test-watch

# Or manually:
pytest tests/unit -v
pytest tests/unit --cov=. --cov-report=html
open htmlcov/index.html  # View coverage
```

**What's being tested:**
- `tests/unit/test_security.py` - JWT, password hashing, auth
- `tests/unit/test_cache.py` - Redis caching logic
- `tests/unit/test_data_validation.py` - Input validation

---

### Job 4: Integration Tests (test-integration)
**What it does:** Tests with real Neo4j and Redis

```bash
# Spins up services:
- neo4j:5-community on port 7687
- redis:7-alpine on port 6379

# Then runs:
pytest tests/integration -v -m integration

# Current Status: ⚠️ OPTIONAL (|| true)
```

**How to run locally:**
```bash
# Start services first
make docker-up

# Run integration tests
make test-integration

# Or manually:
docker-compose up -d neo4j redis
export NEO4J_TEST_URI=bolt://localhost:7687
export NEO4J_TEST_USER=neo4j
export NEO4J_TEST_PASSWORD=password
pytest tests/integration -v -m integration
```

**What's being tested:**
- `tests/integration/test_api_endpoints.py` - Full API tests
- Real database connections
- Cache operations with Redis

---

### Job 5: Docker Build (build-docker)
**What it does:** Builds and tests Docker image

```bash
# Builds:
docker build -t startup-intelligence:test .

# Tests:
docker run --rm startup-intelligence:test python --version
```

**How to run locally:**
```bash
# Build Docker image
make docker-build

# Or manually:
docker build -t startup-intelligence:test .
docker run --rm startup-intelligence:test python --version

# Full stack:
docker-compose build
docker-compose up -d
```

---

### Job 6: Dependencies (dependencies)
**What it does:** Audits package health

```bash
# Checks:
1. pip list --outdated         # Find outdated packages
2. pip install -r requirements.txt --dry-run  # Verify installable
```

**How to run locally:**
```bash
# Check outdated packages
pip list --outdated

# Check for issues
pip check

# Verify requirements
pip install -r requirements.txt --dry-run
```

---

## 🚀 How to Monitor CI/CD Runs

### Method 1: GitHub Actions Web UI (Easiest)

1. **Navigate to Actions tab:**
   ```
   https://github.com/shankerram3/Startup-Intelligence-Analysis-App/actions
   ```

2. **What you'll see:**
   - ✅ Green checkmark = All jobs passed
   - ❌ Red X = One or more jobs failed
   - 🟡 Yellow dot = In progress
   - ⚪ Gray circle = Queued/waiting

3. **Click on a workflow run to see:**
   - Individual job status
   - Logs for each step
   - Artifacts (if any)
   - Time taken per job

4. **Click on a failed job to see:**
   - Which step failed
   - Error messages
   - Full logs

### Method 2: GitHub CLI (Terminal)

```bash
# List recent runs
gh run list --limit 10

# Output:
# ✓  CI/CD Pipeline  main  push  1234567  3m ago
# ✓  CI/CD Pipeline  claude/...  push  1234568  5m ago

# View specific run
gh run view 1234567

# Watch live (updates every 3s)
gh run watch

# View logs
gh run view --log

# View only failed logs
gh run view --log-failed

# Re-run failed jobs
gh run rerun 1234567 --failed
```

### Method 3: Git Commit Badges

Add to your PR or commit message:
```markdown
![CI Status](https://github.com/shankerram3/Startup-Intelligence-Analysis-App/actions/workflows/ci.yml/badge.svg?branch=main)
```

---

## 🐛 Debugging Failed CI/CD Runs

### Step-by-Step Debugging Process

#### 1. Identify Which Job Failed
```bash
gh run view --log-failed
```

#### 2. Read the Error Message
Look for:
- `ERROR:` or `FAILED:` markers
- Exit code (non-zero = failure)
- Python tracebacks
- Test assertion failures

#### 3. Reproduce Locally
```bash
# Example: If "Code Quality" job failed

# Run the exact same command locally:
black --check .

# If it fails, fix it:
black .

# Commit and push:
git add .
git commit -m "fix: code formatting"
git push
```

#### 4. Common Failure Patterns

**Pattern: "Black formatting check failed"**
```bash
# Fix:
make format
git add .
git commit -m "style: format code with black"
git push
```

**Pattern: "Tests failed"**
```bash
# Reproduce:
make test-unit

# Debug:
pytest tests/unit/test_security.py -vv --tb=long

# Fix the code, then:
git add .
git commit -m "fix: resolve test failures"
git push
```

**Pattern: "Docker build failed"**
```bash
# Reproduce:
docker build -t test .

# Common issues:
# - Missing dependencies in requirements.txt
# - Dockerfile syntax errors
# - File not found (check COPY commands)

# Fix and test:
docker build -t test .
git add Dockerfile requirements.txt
git commit -m "fix: docker build issues"
git push
```

**Pattern: "Import errors"**
```bash
# Usually means missing __init__.py or circular imports

# Check:
python -c "import api"
python -c "from utils import security"

# Fix import structure, then push
```

---

## 📊 Understanding CI/CD Status

### What Each Status Means

| Status | Symbol | Meaning | Action |
|--------|--------|---------|--------|
| **Success** | ✅ | All jobs passed | Safe to merge |
| **Failure** | ❌ | One or more jobs failed | Must fix before merge |
| **In Progress** | 🟡 | Jobs still running | Wait for completion |
| **Queued** | ⚪ | Waiting for runner | Be patient |
| **Cancelled** | ⭕ | Manually stopped | Review why |
| **Skipped** | ⏭️ | Job conditions not met | Normal (optional jobs) |

### Job Dependencies

```
code-quality ─┐
security ─────┤
test-unit ────┼─→ ci-success
build-docker ─┘

test-integration ─→ (optional, doesn't block ci-success)
dependencies ─────→ (optional, doesn't block ci-success)
```

**Important:** The `ci-success` job only requires:
- code-quality
- security
- test-unit
- build-docker

Integration tests can fail and CI will still show green! ⚠️

---

## 🔧 Local CI/CD Testing

### Run All CI Checks Locally (Before Pushing)

```bash
# Complete CI simulation
make ci

# Or step by step:
make format-check    # Black + isort
make lint           # Pylint
make type-check     # MyPy
make security-check # Bandit + secrets
make test-unit      # Unit tests
make docker-build   # Docker build
```

### Pre-commit Hooks (Automatic)

Install pre-commit hooks to run checks automatically:

```bash
# Install hooks
make hooks-install

# Or manually:
pip install pre-commit
pre-commit install

# Now every `git commit` will:
# 1. Run black formatting
# 2. Run isort
# 3. Check for large files
# 4. Check for merge conflicts
# 5. Check YAML syntax
```

If checks fail, the commit is rejected. Fix issues and try again.

---

## 📈 Monitoring CI/CD Health

### Key Metrics to Track

1. **Build Success Rate**
   ```bash
   # View last 20 runs
   gh run list --limit 20 | grep "✓" | wc -l
   # Divide by 20 for success rate
   ```

2. **Average Build Time**
   - Check GitHub Actions UI
   - Typical: 5-10 minutes for this project

3. **Flaky Tests**
   - Tests that pass/fail inconsistently
   - Usually in integration tests
   - Current project: Integration tests marked optional due to flakiness

4. **Failed Job Trends**
   - Which jobs fail most often?
   - For this project: Likely integration tests

---

## 🎯 Best Practices for This Project

### Before Pushing Code

```bash
# 1. Run local checks
make format
make test

# 2. Check git status
git status

# 3. Stage changes
git add .

# 4. Commit with descriptive message
git commit -m "feat: add new feature"

# 5. Push
git push

# 6. Monitor CI
gh run watch
```

### Writing Commit Messages

Good commit messages help track CI history:

```bash
# Good:
git commit -m "fix: resolve rate limiting bug in api.py"
git commit -m "test: add unit tests for cache module"
git commit -m "docs: update README with deployment guide"

# Bad:
git commit -m "fixes"
git commit -m "wip"
git commit -m "asdf"
```

### Handling CI Failures

```bash
# 1. Don't force push over failures (unless you know what you're doing)
# 2. Fix the issue locally first
# 3. Run checks locally: make ci
# 4. Push the fix
# 5. Verify CI passes

# If stuck:
gh run view --log-failed  # See what failed
```

---

## 🚨 Current CI/CD Issues (From Review)

### Known Problems

1. **Many jobs allow failures (`|| true`)**
   - Pylint warnings ignored
   - MyPy type errors ignored
   - Security scans don't block
   - Integration tests optional

   **Impact:** CI can show green even with issues

2. **No coverage threshold**
   - Tests run but no minimum coverage enforced
   - Could merge code that reduces coverage

3. **Integration tests flaky**
   - Marked as optional to prevent blocking
   - Should be fixed and made required

### Recommended Fixes

```yaml
# Remove || true from critical checks:
- name: Lint with pylint
  run: |
    pylint api.py pipeline.py rag_query.py graph_builder.py entity_extractor.py utils/ \
    --fail-under=8.0  # Require score >= 8.0

- name: Type check with mypy
  run: |
    mypy api.py pipeline.py rag_query.py --strict  # No ignore-missing-imports

# Add coverage threshold:
- name: Run tests with coverage
  run: |
    pytest --cov=. --cov-fail-under=65  # Require >= 65% coverage
```

---

## 📚 Additional Resources

### GitHub Actions Documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitHub CLI Manual](https://cli.github.com/manual/)

### CI/CD Best Practices
- Keep builds fast (<10 minutes)
- Make builds deterministic (same input = same output)
- Fail fast (run quick checks first)
- Test locally before pushing
- Use caching for dependencies

### Project-Specific Commands

```bash
# Full CI simulation
make ci

# Individual checks
make lint          # Code quality
make test          # All tests
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make security-check    # Security scans
make docker-build      # Docker build test

# Watch tests
make test-watch

# Clean up
make clean
```

---

## 🎬 Example: Following a CI/CD Run

### Scenario: You just pushed a commit

**Step 1: Push triggers CI**
```bash
$ git push origin claude/my-feature
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
...
To github.com:shankerram3/Startup-Intelligence-Analysis-App.git
   abc1234..def5678  claude/my-feature -> claude/my-feature
```

**Step 2: Watch CI start**
```bash
$ gh run watch
Refreshing run status every 3 seconds. Press Ctrl+C to quit.

✓ Code Quality        5s
○ Security           ...
○ Unit Tests         ...
○ Integration Tests  ...
○ Docker Build       ...
○ Dependencies       ...
```

**Step 3: See results**
```bash
$ gh run view

✓ CI/CD Pipeline · def5678
Triggered via push about 3 minutes ago

JOBS
✓ code-quality      1m 23s
✓ security          1m 45s
✓ test-unit         2m 12s
✓ test-integration  2m 34s
✓ build-docker      1m 56s
✓ dependencies      0m 45s
✓ ci-success        0m 12s

✓ All checks passed
```

**Step 4: If failure occurs**
```bash
$ gh run view --log-failed

✗ test-unit
  Run pytest tests/unit -v

  tests/unit/test_security.py::test_create_token FAILED

  AssertionError: Token expiration incorrect
  Expected: 3600
  Got: 3599
```

**Step 5: Fix and re-push**
```bash
# Fix the issue locally
$ vim tests/unit/test_security.py

# Test the fix
$ pytest tests/unit/test_security.py -v
... all tests pass ...

# Commit and push
$ git add tests/unit/test_security.py
$ git commit -m "fix: adjust token expiration test tolerance"
$ git push

# Watch CI again
$ gh run watch
```

---

## 📞 Quick Reference Card

```bash
# View CI status
gh run list --limit 5              # Recent runs
gh run view                        # Latest run details
gh run watch                       # Live monitoring
gh run view --log-failed           # Failed job logs

# Run checks locally
make ci                            # All checks
make test                          # All tests
make format                        # Auto-format code
make lint                          # Linting only
make security-check                # Security scans

# Docker operations
make docker-up                     # Start services
make docker-down                   # Stop services
make docker-logs                   # View logs
make docker-restart                # Restart services

# Debugging
pytest -vv --tb=long              # Verbose test output
pytest --lf                       # Run last failed tests
pytest -k test_name               # Run specific test
docker-compose logs -f service    # Follow service logs
```

---

**Need Help?**
- Check CI logs: `gh run view --log`
- Run locally: `make ci`
- Review errors: `gh run view --log-failed`
- Ask for help with specific error messages

**Happy CI/CD monitoring!** 🚀
