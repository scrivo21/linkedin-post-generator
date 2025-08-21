# Contributing to LinkedIn Post Generator

```ascii
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   🤝 Thank you for contributing to LinkedIn Post Generator! 🤝  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

We love your input! We want to make contributing to LinkedIn Post Generator as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Community](#community)

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome people of all backgrounds and skill levels
- **Be collaborative**: Work together constructively
- **Be helpful**: Offer assistance and share knowledge
- **Be patient**: Everyone is learning and growing

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Discord Bot Token
- LinkedIn Developer Account
- Git

### Local Development Setup

1. **Fork the Repository**
   ```bash
   # Fork the repo on GitHub, then clone your fork
   git clone https://github.com/yourusername/linkedin-post-generator.git
   cd linkedin-post-generator
   ```

2. **Set up Development Environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Additional dev tools
   ```

3. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit with your test credentials (never use production credentials!)
   nano .env
   ```

4. **Set up Database**
   ```bash
   # Create test database
   createdb linkedin_test
   psql linkedin_test < schema.sql
   ```

5. **Verify Setup**
   ```bash
   # Run tests to ensure everything is working
   pytest
   
   # Start the bot in development mode
   python discord_linkedin_bot.py
   ```

## 🔄 Development Process

### Branching Strategy

We use a simplified Git Flow:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features and enhancements
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes

### Workflow

1. **Create a Branch**
   ```bash
   # For new features
   git checkout -b feature/amazing-new-feature
   
   # For bug fixes
   git checkout -b bugfix/fix-discord-issue
   
   # For hotfixes
   git checkout -b hotfix/critical-security-fix
   ```

2. **Make Your Changes**
   - Write clean, well-documented code
   - Follow our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run the full test suite
   pytest
   
   # Run linting and formatting
   black .
   isort .
   flake8
   
   # Type checking
   mypy *.py
   ```

4. **Commit Your Changes**
   ```bash
   # Use conventional commit format
   git commit -m "feat: add LinkedIn post scheduling feature"
   git commit -m "fix: resolve Discord bot connection timeout"
   git commit -m "docs: update API documentation"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/amazing-new-feature
   # Then create a Pull Request on GitHub
   ```

## 📝 Pull Request Process

### Before Submitting

1. **Update Documentation**: Ensure README, docstrings, and relevant docs are updated
2. **Add Tests**: Include tests for new features and bug fixes
3. **Run Full Test Suite**: Make sure all tests pass locally
4. **Check Dependencies**: Only add necessary dependencies
5. **Security Review**: Ensure no sensitive data is exposed

### PR Requirements

- [ ] Clear title and description
- [ ] Links to related issues
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Approved by at least one maintainer

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and security scans
2. **Code Review**: Maintainers review for code quality, security, and design
3. **Testing**: Manual testing if needed
4. **Approval**: At least one approval from maintainers
5. **Merge**: Squash and merge to main branch

## 📏 Coding Standards

### Python Style Guide

We follow PEP 8 with some project-specific conventions:

```python
# Good: Clear function with type hints and docstring
async def approve_post(post_id: str, approver: str) -> bool:
    """
    Approve a LinkedIn post for publishing.
    
    Args:
        post_id: Unique identifier for the post
        approver: Discord username of the approver
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        result = await db.update_post_status(post_id, "approved")
        logger.info(f"Post {post_id} approved by {approver}")
        return result
    except Exception as e:
        logger.error(f"Failed to approve post {post_id}: {e}")
        return False

# Bad: No type hints, unclear naming, no error handling
def approve(id, user):
    db.update(id, "approved")
    return True
```

### Key Conventions

- **Type Hints**: Always use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions
- **Error Handling**: Proper exception handling with logging
- **Logging**: Use structured logging with appropriate levels
- **Constants**: Use UPPER_CASE for constants
- **Private Methods**: Use leading underscore for private methods

### Code Formatting

We use automated tools for consistent formatting:

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Check style with flake8
flake8

# Type checking with mypy
mypy *.py
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── test_models.py
│   ├── test_discord_bot.py
│   └── test_linkedin_api.py
├── integration/       # Integration tests
│   ├── test_approval_workflow.py
│   └── test_database_operations.py
├── fixtures/          # Test data
│   ├── sample_posts.json
│   └── mock_responses.py
└── conftest.py        # Pytest configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from models import Post, PostStatus

class TestPostApproval:
    """Test post approval functionality."""
    
    @pytest.fixture
    async def sample_post(self):
        """Create a sample post for testing."""
        return Post(
            id="test-123",
            content="Test LinkedIn post",
            status=PostStatus.PENDING,
            industry="Technology"
        )
    
    @patch('linkedin_api.publish_post')
    async def test_approve_post_success(self, mock_publish, sample_post):
        """Test successful post approval."""
        mock_publish.return_value = {"success": True, "id": "linkedin-123"}
        
        result = await approve_post(sample_post.id, "testuser")
        
        assert result is True
        mock_publish.assert_called_once()
        
    async def test_approve_nonexistent_post(self):
        """Test approval of non-existent post fails gracefully."""
        result = await approve_post("nonexistent", "testuser")
        assert result is False
```

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Test system performance under load

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_discord_bot.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"
```

## 📚 Documentation Guidelines

### Types of Documentation

1. **Code Comments**: Explain complex logic and decisions
2. **Docstrings**: Document all public functions, classes, and modules
3. **README**: Keep project overview up-to-date
4. **API Documentation**: Document all endpoints and responses
5. **User Guides**: Step-by-step instructions for users

### Documentation Standards

```python
class LinkedInBot:
    """
    Discord bot for LinkedIn post approval workflow.
    
    This bot monitors a PostgreSQL database for pending LinkedIn posts,
    sends them to Discord for team approval, and automatically publishes
    approved posts to LinkedIn.
    
    Attributes:
        approval_channel: Discord channel for post approvals
        notification_channel: Discord channel for notifications
        
    Example:
        >>> bot = LinkedInBot()
        >>> await bot.setup_channels()
        >>> await bot.send_approval_request(post)
    """
    
    async def send_approval_request(self, post: Post) -> bool:
        """
        Send a LinkedIn post to Discord for team approval.
        
        Creates a rich embed with post preview, analytics, and approval
        buttons. The post is sent to the configured approval channel.
        
        Args:
            post: The LinkedIn post to send for approval
            
        Returns:
            True if the approval request was sent successfully
            
        Raises:
            DiscordError: If Discord API call fails
            DatabaseError: If database update fails
            
        Example:
            >>> success = await bot.send_approval_request(my_post)
            >>> if success:
            ...     print("Approval request sent!")
        """
        # Implementation here...
```

## 🎯 Issue Guidelines

### Reporting Bugs

Use our bug report template and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment information
- Relevant logs or error messages

### Feature Requests

Use our feature request template and include:

- Problem the feature solves
- Proposed solution
- Alternative solutions considered
- Use cases and benefits

### Questions

Use our question template for:

- Usage questions
- Configuration help
- Troubleshooting assistance
- Clarifications about features

## 🔧 Development Tools

### Recommended IDE Setup

#### VS Code
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true
}
```

#### PyCharm
- Configure interpreter to use project venv
- Enable Black formatter
- Configure isort with Black profile
- Enable mypy type checking

### Useful Commands

```bash
# Development shortcuts
make install     # Install dependencies
make test        # Run tests
make lint        # Run linting and formatting
make clean       # Clean temporary files
make docs        # Generate documentation

# Or manually:
pip install -e .                    # Install in development mode
pytest --watch                      # Run tests on file changes
black --check .                     # Check formatting without fixing
mypy --install-types --non-interactive  # Install missing type stubs
```

## 🚀 Deployment and Release

### Release Process

1. **Create Release Branch**
   ```bash
   git checkout -b release/v1.2.0
   ```

2. **Update Version Numbers**
   - Update version in `__version__.py`
   - Update CHANGELOG.md
   - Update documentation

3. **Final Testing**
   - Run full test suite
   - Manual testing of critical paths
   - Security scan

4. **Create Pull Request**
   - Target main branch
   - Include release notes
   - Get maintainer approval

5. **Tag and Release**
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

## 🤖 CI/CD Pipeline

Our GitHub Actions pipeline includes:

- **Lint and Format**: Black, isort, flake8
- **Type Checking**: mypy
- **Security Scanning**: bandit, safety, semgrep  
- **Testing**: pytest with coverage reporting
- **Docker Build**: Multi-stage builds for production
- **Documentation**: Auto-generate and deploy docs

## 📞 Getting Help

### Community Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Discord Server**: [Join our Discord](https://discord.gg/example) (coming soon)

### Maintainers

- [@maintainer1](https://github.com/maintainer1) - Lead maintainer
- [@maintainer2](https://github.com/maintainer2) - Discord bot specialist
- [@maintainer3](https://github.com/maintainer3) - LinkedIn API integration

## 🏆 Recognition

Contributors are recognized in several ways:

- **All Contributors**: Listed in README.md
- **Major Contributors**: Special recognition in releases
- **Maintainers**: Invited to join the core team
- **Community Champions**: Special badges and mentions

## 📈 Project Roadmap

Check out our [Native App Implementation Plan](NATIVE_APP_IMPLEMENTATION_PLAN.md) for upcoming features:

- Native iOS and macOS applications
- Enhanced mobile experience
- Offline synchronization
- Push notifications
- Biometric authentication

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

## 🙏 Thank You!

Every contribution, no matter how small, makes a difference. Whether you're fixing a typo, reporting a bug, or building a major feature, your help makes LinkedIn Post Generator better for everyone.

**Happy Contributing!** 🎉

---

<p align="center">
  <strong>Made with ❤️ by the LinkedIn Post Generator community</strong>
</p>