# Contributing to Social Styles Assessment

Thank you for considering contributing to the Social Styles Assessment project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please create an issue with the following information:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Screenshots if applicable
- Any relevant details about your environment

### Suggesting Enhancements

If you have ideas for enhancements, please create an issue with:
- A clear, descriptive title
- A detailed description of the proposed enhancement
- Any relevant mockups or examples
- Why this enhancement would be useful to most users

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Open a Pull Request

## Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/[username]/social-styles-assessment.git
   cd social-styles-assessment
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python initialize_assessment.py
   ```

5. Run the application:
   ```
   flask run
   ```

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

### Python Styleguide

- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Use docstrings for functions and classes
- Keep functions focused on a single responsibility

### HTML/CSS Styleguide

- Use 2 spaces for indentation in HTML and CSS files
- Use semantic HTML elements
- Follow Bootstrap conventions when applicable

## Additional Notes

### Issue and Pull Request Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed

Thank you for contributing to the Social Styles Assessment project! 