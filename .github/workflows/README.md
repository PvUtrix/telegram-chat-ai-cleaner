# GitHub Actions Workflows

This directory contains automated CI/CD and security workflows for the project.

## Workflows

### 1. CI (ci.yml)

**Trigger**: Push and Pull Requests to main/master
**Purpose**: Continuous Integration - code quality and testing

**Jobs**:
- **Linting**: ruff, black
- **Type Checking**: mypy
- **Testing**: pytest with coverage
- **Build**: Package building and validation
- **Caching**: pip package caching for faster builds

**Matrix**: Python 3.9, 3.10, 3.11, 3.12

### 2. Security (security.yml)

**Trigger**: Push, Pull Requests, and weekly schedule (Mondays)
**Purpose**: Comprehensive security scanning

**Jobs**:

#### Dependency Scan
- **Safety**: PyUp.io vulnerability scanner
- **pip-audit**: PyPA vulnerability scanner
- Checks all dependencies against CVE database

#### Security Scan
- **Bandit**: Python security linter
- Detects common security issues
- Generates JSON report

#### Secrets Scan
- **Gitleaks**: Secrets detection
- Scans git history for leaked credentials
- Prevents accidental secret commits

#### CodeQL Analysis
- **GitHub CodeQL**: Semantic code analysis
- Detects complex security vulnerabilities
- Security and quality queries

#### Semgrep
- **Semgrep**: Pattern-based security scan
- Fast static analysis
- OWASP Top 10 detection

#### License Check
- **pip-licenses**: License compliance
- Generates license reports
- Ensures open-source compliance

#### SBOM Generation
- **CycloneDX**: Software Bill of Materials
- Tracks all dependencies
- Supply chain security

### 3. OpenSSF Scorecard (scorecard.yml)

**Trigger**: Push, Pull Requests, and weekly schedule (Saturdays)
**Purpose**: Security health metrics

**Checks**:
- Branch protection
- Code review requirements
- Dependency updates
- Vulnerability disclosure
- Security policy
- Token permissions
- Signed commits

**Results**: Uploaded to GitHub Security tab

## Workflow Permissions

All workflows use minimal required permissions following the principle of least privilege:

- `contents: read` - Read repository contents
- `security-events: write` - Write security scan results
- `actions: read` - Read workflow runs
- `id-token: write` - OIDC token for scorecard

## Artifacts

### CI Workflow
- `dist-packages`: Built Python packages (Python 3.11 only)
- `coverage.xml`: Code coverage report

### Security Workflow
- `bandit-results`: Security scan results (JSON)
- `semgrep-results`: Semgrep scan results (JSON)
- `license-report`: License compliance report (MD + JSON)
- `sbom`: Software Bill of Materials (JSON + XML)

## Caching

The CI workflow uses GitHub Actions cache to speed up builds:
- **Cache Key**: `${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}`
- **Cache Path**: `~/.cache/pip`
- Restores on cache hit, rebuilds on miss

## Error Handling

Some steps use `continue-on-error: true` for non-critical checks:
- Linting (ruff, black) - Warnings don't fail build
- Type checking (mypy) - Optional for now
- Security scans - Report issues but don't block

This ensures the CI pipeline doesn't fail on minor issues while still reporting them.

## Adding New Workflows

To add a new workflow:

1. Create `.github/workflows/your-workflow.yml`
2. Define trigger events
3. Set appropriate permissions
4. Add jobs and steps
5. Use caching where appropriate
6. Add artifacts for reports
7. Document in this README

### Example Workflow Template

```yaml
name: Your Workflow

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

permissions:
  contents: read

jobs:
  your-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Your Step
        run: echo "Hello"
```

## Debugging Workflows

### View Workflow Runs
1. Go to **Actions** tab in GitHub
2. Select the workflow
3. Click on a specific run
4. View logs and artifacts

### Run Locally

```bash
# Install act (https://github.com/nektos/act)
brew install act  # macOS
# or download binary

# Run workflow locally
act -j build  # Run specific job
act pull_request  # Simulate PR event
```

### Troubleshooting

**Common Issues**:

1. **Cache Miss**: Delete cache and let it rebuild
2. **Permission Denied**: Check workflow permissions
3. **Timeout**: Increase timeout or optimize steps
4. **Failed Dependencies**: Check requirements.txt

## Security Considerations

- **Secrets**: Never log secrets or expose them
- **Permissions**: Use minimal required permissions
- **Third-party Actions**: Pin to specific SHA or major version
- **GITHUB_TOKEN**: Automatically provided, limited scope
- **External Services**: Use with caution

## Monitoring

Monitor workflow health:
- Check success rates
- Review security scan results
- Update dependencies regularly
- Keep workflow actions up to date

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [OpenSSF Scorecard](https://github.com/ossf/scorecard)
- [CodeQL](https://codeql.github.com/)
- [Semgrep](https://semgrep.dev/)
- [Gitleaks](https://github.com/gitleaks/gitleaks)

---

**Last Updated**: 2025-01-05
