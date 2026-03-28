English | [简体中文](CONTRIBUTING.zh.md)

# Contributing to littledl

First off, thank you for considering contributing to littledl! It's people like you that make this project great.

## Table of Contents

- [Contributing to littledl](#contributing-to-littledl)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Development Setup](#development-setup)
  - [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Pull Requests](#pull-requests)
  - [Coding Standards](#coding-standards)
    - [Python Style](#python-style)
  - [Commit Guidelines](#commit-guidelines)
    - [Format](#format)
    - [Types](#types)
  - [Pull Request Process](#pull-request-process)
  - [Additional Resources](#additional-resources)
  - [Questions?](#questions)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/little-tree-downloader.git
cd little-tree-downloader
```

2. **Install dependencies**

```bash
uv sync --all-extras
```

3. **Run tests to verify setup**

```bash
uv run pytest tests/ -v
```

4. **Run linting**

```bash
uv run ruff check src/
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples with code snippets**
- **Describe the behavior you observed and expected**
- **Include your environment details** (OS, Python version, package version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the use case**
- **Describe the current behavior and explain the expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

1. **Create a branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

2. **Make your changes**

- Follow the [coding standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed

3. **Run tests and linting**

```bash
uv run pytest tests/ -v --cov
uv run ruff check src/
```

4. **Commit your changes**

Follow the [commit guidelines](#commit-guidelines).

5. **Push and create a pull request**

```bash
git push origin your-branch-name
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Write docstrings for public modules, functions, classes, and methods
- Maximum line length is 120 characters


## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

## Pull Request Process

1. **Ensure all tests pass** before submitting
2. **Update documentation** for any new features
3. **Add tests** for any new functionality
4. **Follow the PR template** when creating your PR
5. **Request review** from maintainers
6. **Address review feedback** promptly

## Additional Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [httpx Documentation](https://www.python-httpx.org/)
- [flet Documentation](https://docs.flet.dev/)
- [uv Documentation](https://docs.astral.sh/uv/)

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.

Thank you for contributing!
