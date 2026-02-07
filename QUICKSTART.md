# Quick Start Guide

Get started with the Terraform Version Checker Action in 5 minutes!

## Step 1: Add to Your Repository

### Option A: Use from GitHub (Recommended)

Once you publish this action to GitHub:

```yaml
# .github/workflows/terraform-version-check.yml
name: Check Terraform Versions

on:
  pull_request:
  push:
    branches: [main]

jobs:
  check-versions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: your-username/terraform-version-checker-action@v1
```

### Option B: Copy to Your Repository

1. Copy the action files to `.github/actions/terraform-version-checker/` in your repo
2. Use it as a local action:

```yaml
# .github/workflows/terraform-version-check.yml
name: Check Terraform Versions

on:
  pull_request:
  push:
    branches: [main]

jobs:
  check-versions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/terraform-version-checker
```

## Step 2: Customize (Optional)

### Check Specific Directories

```yaml
- uses: your-username/terraform-version-checker-action@v1
  with:
    directory: |
      ./infrastructure
      ./modules
```

### Fail on Outdated Versions

```yaml
- uses: your-username/terraform-version-checker-action@v1
  with:
    fail-on-updates: 'true'
```

## Step 3: Run and Review

The action will:
1. ✅ Fetch the latest Terraform version
2. 🔍 Scan your files for version specifications
3. 📊 Generate a detailed report
4. 💡 Suggest updates

## Example Output

```
📦 Terraform Version Check Report
Latest stable version: 1.10.0

📄 File: .terraform-version
  • Current: 1.5.0
  • Latest:  1.10.0
  • ⚠️  Update recommended

📊 Summary: 1 update(s) recommended
```

## What Files Are Checked?

- `.terraform-version` - Direct version specifications
- `*.tf` files - `required_version` constraints in terraform blocks

## Common Workflows

### Weekly Scheduled Check

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday at 9am
```

### Auto-Create Issues

```yaml
- name: Create issue
  if: steps.check.outputs.updates_found == 'true'
  uses: actions/github-script@v7
  # ... (see README for full example)
```

### PR Comments

```yaml
- name: Comment on PR
  if: github.event_name == 'pull_request'
  # ... (see README for full example)
```

## Next Steps

- 📖 Read the [full README](README.md) for advanced usage
- 🔧 Check the [example workflows](.github/workflows/terraform-version-check.yml)
- 🤝 See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Need Help?

- 📝 Check the [README](README.md) for detailed documentation
- 🐛 [Report issues](https://github.com/your-username/terraform-version-checker-action/issues)
- 💬 Ask questions in discussions

## Publishing the Action

To publish on GitHub Marketplace:

1. Push to GitHub
2. Create a release (e.g., `v1.0.0`)
3. Add a tag
4. Publish to GitHub Marketplace

```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```
