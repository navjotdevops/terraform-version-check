# Test Examples

This directory contains example Terraform files for testing the action.

## Directory Structure

```
examples/
├── basic/
│   ├── .terraform-version
│   └── main.tf
├── multi-module/
│   ├── module1/
│   │   ├── .terraform-version
│   │   └── main.tf
│   └── module2/
│       ├── .terraform-version
│       └── versions.tf
└── constraints/
    └── main.tf
```

## Test Cases

### Basic Example
Simple case with both `.terraform-version` and `required_version`.

### Multi-Module Example
Multiple modules with different version specifications.

### Constraints Example
Various constraint formats:
- `>= 1.5.0`
- `~> 1.5`
- `= 1.5.0`

## Running Tests

```bash
# Test basic example
python terraform_version_checker.py --directory examples/basic

# Test all examples
python terraform_version_checker.py --directory examples
```
