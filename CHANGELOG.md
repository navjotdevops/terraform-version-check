# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-07

### Added
- Initial release of Terraform Version Checker Action
- Check `.terraform-version` files for outdated versions
- Check `required_version` constraints in Terraform files
- Fetch latest stable Terraform version from HashiCorp releases API
- Support for multiple directory scanning
- Detailed reporting with update recommendations
- GitHub Actions outputs for automation
- Optional fail-on-updates mode
- Docker-based action for consistent execution
- Comprehensive documentation and examples

### Features
- Automatic version parsing and comparison
- Support for various constraint formats (>=, ~>, =)
- Structured JSON output for programmatic access
- Example workflows for common use cases
- Integration examples with GitHub Issues and PR comments

## [Unreleased]

### Planned
- Support for checking Terraform provider versions
- Support for checking Terraform module versions
- Auto-fix mode to automatically update version files
- Configurable version constraint update strategies
- Support for custom version registries
