# Terraform Version Checker Action

A GitHub Action that automatically checks your Terraform version specifications and suggests upgrades to the latest stable version.

## Features

- ✅ Checks `.terraform-version` files
- ✅ Checks `required_version` constraints in Terraform files
- ✅ Fetches latest stable Terraform version from HashiCorp
- ✅ **Configurable patch offset** - Target N patches behind latest (e.g., 1.14.2 instead of 1.14.4)
- ✅ Tracks current versions in use
- ✅ Supports multiple directory scanning
- ✅ Generates detailed reports
- ✅ Optionally fails workflow if updates are needed
- ✅ Provides structured outputs for further automation

## Usage

### Basic Usage

```yaml
name: Check Terraform Versions

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    # Run weekly on Monday at 9am UTC
    - cron: '0 9 * * 1'

jobs:
  terraform-version-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Check Terraform versions
        uses: navjotdevops/terraform-version-checker-action@v1
        with:
          directory: '.'
```

### Advanced Usage

#### Check Multiple Directories

```yaml
- name: Check Terraform versions
  uses: navjotdevops/terraform-version-checker-action@v1
  with:
    directory: |
      ./infrastructure/aws
      ./infrastructure/gcp
      ./modules/networking
```

#### Fail on Outdated Versions

```yaml
- name: Check Terraform versions
  uses: navjotdevops/terraform-version-checker-action@v1
  with:
    directory: '.'
    fail-on-updates: 'true'
```

#### Target Specific Patch Version

By default, the action targets 2 patch versions behind the latest. You can customize this:

```yaml
- name: Check Terraform versions
  uses: navjotdevops/terraform-version-checker-action@v1
  with:
    directory: '.'
    patches-behind: '2'  # If latest is 1.14.4, this will suggest 1.14.2
```

Set to `0` to always use the absolute latest:

```yaml
- name: Check Terraform versions
  uses: navjotdevops/terraform-version-checker-action@v1
  with:
    patches-behind: '0'  # Use the absolute latest version
```

#### Create Issue for Updates

```yaml
- name: Check Terraform versions
  id: tf-check
  uses: navjotdevops/terraform-version-checker-action@v1
  with:
    directory: '.'

- name: Create issue if updates found
  if: steps.tf-check.outputs.updates_found == 'true'
  uses: actions/github-script@v7
  with:
    script: |
      const findings = JSON.parse('${{ steps.tf-check.outputs.findings }}');
      const latestVersion = '${{ steps.tf-check.outputs.latest_version }}';
      const currentVersion = '${{ steps.tf-check.outputs.current_version }}';
      
      let body = `## Terraform Version Update Available\n\n`;
      body += `- Current version: **${currentVersion}**\n`;
      body += `- Target version: **${latestVersion}**\n\n`;
      body += `Found ${findings.length} file(s) that can be updated:\n\n`;
      
      findings.forEach(finding => {
        body += `### ${finding.file}\n`;
        if (finding.type === 'terraform-version-file') {
          body += `- Current: ${finding.current_version}\n`;
          body += `- Target: ${finding.latest_version}\n`;
        } else {
          body += `- Current constraint: \`${finding.current_constraint}\`\n`;
          body += `- Current version: ${finding.current_version}\n`;
          body += `- Target: ${finding.latest_version}\n`;
          body += `- Suggested: \`${finding.suggested_constraint}\`\n`;
        }
        body += '\n';
      });
      
      await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `feat: Update Terraform to v${latestVersion}`,
        body: body,
        labels: ['terraform', 'dependencies']
      });
```

#### Post Comment on PR

```yaml
- name: Check Terraform versions
  id: tf-check
  uses: navjotdevops/terraform-version-checker-action@v1
  with:
    directory: '.'

- name: Comment on PR
  if: steps.tf-check.outputs.updates_found == 'true' && github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const updateCount = '${{ steps.tf-check.outputs.update_count }}';
      const latestVersion = '${{ steps.tf-check.outputs.latest_version }}';
      const currentVersion = '${{ steps.tf-check.outputs.current_version }}';
      
      const message = `## ⚠️ Terraform Version Update Available

Current version **${currentVersion}** can be updated to **${latestVersion}**.

Found ${updateCount} file(s) that need updating.

Please review the action logs for details.`;
      
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: message
      });
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `directory` | Directory to scan (supports multiple paths separated by newlines) | No | `.` |
| `token` | GitHub token for API access | No | `${{ github.token }}` |
| `fail-on-updates` | Fail the action if updates are found | No | `false` |
| `patches-behind` | Number of patch versions behind latest to target | No | `2` |

## Outputs

| Output | Description |
|--------|-------------|
| `updates_found` | Whether any outdated versions were found (`true`/`false`) |
| `update_count` | Number of version updates recommended |
| `current_version` | Current Terraform version(s) found in the repository |
| `latest_version` | Target Terraform version (patches-behind from latest) |
| `findings` | JSON array of all findings with details |

## How It Works

1. **Fetches Target Version**: Queries HashiCorp's releases API and calculates target version based on `patches-behind` parameter
2. **Scans Files**: Looks for:
   - `.terraform-version` files (exact version specifications)
   - `required_version` constraints in `*.tf` files
3. **Compares Versions**: Parses version constraints and compares with target version
4. **Reports Findings**: Generates a detailed report with update recommendations

## Example Output

```
🔍 Fetching latest Terraform version...
✅ Latest stable Terraform version: 1.10.0

🔍 Scanning directory: /github/workspace

📦 Terraform Version Check Report
Latest stable version: 1.10.0

================================================================================

📄 File: .terraform-version
  • .terraform-version file
    Current: 1.5.0
    Latest:  1.10.0
    ⚠️  Update recommended

📄 File: main.tf
  • required_version constraint
    Current: >= 1.5.0
    Version: 1.5.0
    Latest:  1.10.0
    Suggested: >= 1.10.0
    ⚠️  Update recommended

================================================================================

📊 Summary: 2 update(s) recommended
```

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python terraform_version_checker.py --directory ./path/to/terraform/code
```

### Testing

Create test Terraform files:

```bash
# Create test directory
mkdir -p test/terraform

# Create .terraform-version file
echo "1.5.0" > test/terraform/.terraform-version

# Create main.tf with required_version
cat > test/terraform/main.tf << 'EOF'
terraform {
  required_version = ">= 1.5.0"
}
EOF

# Run the checker
python terraform_version_checker.py --directory test/terraform
```

## Version Detection

The action detects versions in:

### `.terraform-version` files
```
1.5.0
```

### Terraform blocks with `required_version`
```hcl
terraform {
  required_version = ">= 1.5.0"
}

terraform {
  required_version = "~> 1.5"
}

terraform {
  required_version = "= 1.5.0"
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Related Projects

- [terraform-module-versions-action](https://github.com/trumant/terraform-module-versions-action) - Checks Terraform module versions
- [setup-terraform](https://github.com/hashicorp/setup-terraform) - Sets up Terraform CLI

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/navjotdevops/terraform-version-checker-action/issues).
