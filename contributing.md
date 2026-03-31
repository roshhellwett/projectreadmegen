# Contributing to projectreadmegen

Thank you for your interest in contributing! This project welcomes contributions from the community.

## How to Contribute

### Fork the Repository

1. Click the "Fork" button on GitHub
2. Clone your forked repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/projectreadmegen.git
   cd projectreadmegen
   ```

### Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Make Your Changes

```bash
# Create a new branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests
pytest tests/ -v

# Commit your changes
git add .
git commit -m "Add your feature description"
```

### Submit a Pull Request

1. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub

3. Fill in the PR template with:
   - Description of your changes
   - Related issue number (if applicable)
   - Testing performed

## Coding Standards

- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Keep functions focused and simple
- Write tests for new features

## Types of Contributions

- **Bug fixes**: Report issues on GitHub first
- **New features**: Open an issue to discuss before implementing
- **Documentation**: Improvements always welcome
- **Tests**: Increase test coverage

## Get Help

- Open an issue: https://github.com/roshhellwett/projectreadmegen/issues
- Email: roshhellwett@icloud.com

---

**Powered by Zenith Open Source Projects | Developer - roshhellwett**
