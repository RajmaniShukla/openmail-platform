# Contributing to OpenMail

Thank you for your interest in contributing to OpenMail! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/openmail-platform.git
   cd openmail-platform
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start development services**
   ```bash
   docker compose up -d postgres redis elasticsearch
   ```

4. **Backend development**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

5. **Frontend development**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📝 Code Style

### Python (Backend)

- Follow PEP 8 guidelines
- Use type hints
- Format with `black`
- Sort imports with `isort`
- Lint with `flake8`

```bash
# Format code
black app/
isort app/

# Check linting
flake8 app/
mypy app/
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Follow ESLint rules
- Use Prettier for formatting

```bash
# Lint and format
npm run lint
npm run format
```

## 🔀 Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, descriptive commits
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass**
6. **Submit a pull request**

### PR Guidelines

- Use a clear, descriptive title
- Reference any related issues
- Include screenshots for UI changes
- Keep changes focused and atomic

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(email): add attachment preview`
- `fix(auth): resolve token refresh issue`
- `docs(readme): update installation steps`

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## 📁 Project Structure

```
openmail-platform/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Config, security
│   │   ├── db/       # Database
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── tests/
├── frontend/          # Next.js frontend
│   ├── src/
│   │   ├── app/      # Pages
│   │   ├── components/
│   │   ├── lib/      # Utilities
│   │   └── stores/   # State management
│   └── tests/
├── mailserver/        # Mail server configs
├── monitoring/        # Prometheus & Grafana
└── scripts/           # Deployment scripts
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description** of the issue
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **Environment** (OS, browser, versions)
6. **Screenshots** if applicable

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Describe the use case
3. Explain the proposed solution
4. Consider backward compatibility

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the issue, not the person
- Help others learn and grow

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Every contribution helps make OpenMail better. Thank you for being part of our community!
