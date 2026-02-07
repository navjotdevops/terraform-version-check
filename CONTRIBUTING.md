# Contributing to Terraform Version Checker Action

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/terraform-version-checker-action.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes locally
6. Commit your changes: `git commit -am 'Add new feature'`
7. Push to the branch: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip
- Docker (for testing the Docker image)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script locally
python terraform_version_checker.py --directory ./examples/basic

# Test with multiple directories
python terraform_version_checker.py --directory examples
```

### Testing

Before submitting a PR, please test your changes:

```bash
# Test with basic example
python terraform_version_checker.py --directory examples/basic

# Test with constraints example
python terraform_version_checker.py --directory examples/constraints

# Test fail-on-updates flag
python terraform_version_checker.py --directory examples/basic --fail-on-updates
```

### Building the Docker Image

```bash
# Build the Docker image
docker build -t terraform-version-checker .

# Test the Docker image
docker run --rm -v $(pwd)/examples:/github/workspace terraform-version-checker --directory /github/workspace/basic
```

## Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise
- Add comments for complex logic

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the CHANGELOG.md with your changes under the `[Unreleased]` section
3. Ensure all tests pass
4. Update documentation if you're adding new features
5. Your PR will be reviewed by maintainers

## Reporting Issues

When reporting issues, please include:

- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Relevant log output or error messages

## Feature Requests

We welcome feature requests! Please:

- Check if the feature has already been requested
- Provide a clear description of the feature
- Explain the use case and benefits
- Consider contributing the feature yourself

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Questions?

If you have questions, feel free to:

- Open an issue with the "question" label
- Reach out to the maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
