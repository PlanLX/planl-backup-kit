# PlanLX Backup Kit Documentation

Welcome to the PlanLX Backup Kit documentation! This directory contains comprehensive documentation for all aspects of the project.

## 📚 Documentation Structure

### Getting Started
- **[Quick Start Guide](quick-start.md)** - Get up and running in minutes
- **[Installation Guide](installation.md)** - Detailed installation instructions
- **[Configuration Guide](configuration.md)** - Complete configuration reference

### User Guides
- **[Elasticsearch Backup](elasticsearch/)** - Elasticsearch backup and restore
- **[MySQL Backup](mysql/)** - MySQL backup and restore (coming soon)
- **[PostgreSQL Backup](postgresql/)** - PostgreSQL backup and restore (coming soon)
- **[MongoDB Backup](mongodb/)** - MongoDB backup and restore (coming soon)

### Deployment
- **[Docker Deployment](deployment/docker.md)** - Containerized deployment
- **[Kubernetes Deployment](deployment/kubernetes.md)** - K8s deployment guide
- **[CI/CD Pipeline](deployment/cicd.md)** - GitHub Actions setup

### API Reference
- **[API Documentation](api/)** - Complete API reference
- **[CLI Reference](cli/)** - Command-line interface reference
- **[Configuration Schema](api/config-schema.md)** - Configuration file schema

### Development
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute
- **[Development Setup](development/setup.md)** - Development environment
- **[Testing Guide](development/testing.md)** - Testing procedures
- **[Release Process](development/release.md)** - Release procedures

### Troubleshooting
- **[Common Issues](troubleshooting/common-issues.md)** - Frequently encountered problems
- **[Debugging Guide](troubleshooting/debugging.md)** - Debugging techniques
- **[Performance Tuning](troubleshooting/performance.md)** - Performance optimization

## 🚀 Quick Navigation

### For Users
1. Start with the [Quick Start Guide](quick-start.md)
2. Read the [Configuration Guide](configuration.md)
3. Choose your deployment method: [Docker](deployment/docker.md) or [Kubernetes](deployment/kubernetes.md)

### For Developers
1. Read the [Contributing Guide](../CONTRIBUTING.md)
2. Set up your [Development Environment](development/setup.md)
3. Review the [API Documentation](api/)

### For Operators
1. Review [Deployment Guides](deployment/)
2. Check [Troubleshooting](troubleshooting/)
3. Monitor with [Performance Tuning](troubleshooting/performance.md)

## 📖 Documentation Standards

### Writing Guidelines
- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Add troubleshooting sections
- Keep documentation up to date

### Code Examples
- Use syntax highlighting
- Include complete, runnable examples
- Show both simple and advanced use cases
- Provide configuration examples

### Structure
- Start with user goals
- Progress from simple to complex
- Include cross-references
- Maintain consistent formatting

## 🔄 Contributing to Documentation

We welcome contributions to improve our documentation! Please see our [Contributing Guide](../CONTRIBUTING.md) for details.

### Documentation Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the documentation locally
5. Submit a pull request

### Local Documentation Testing
```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## 📞 Getting Help

- **Documentation Issues**: Create an issue with the `documentation` label
- **Questions**: Use [GitHub Discussions](https://github.com/PlanLX/planl-backup-kit/discussions)
- **Bugs**: Use the [Bug Report Template](../.github/ISSUE_TEMPLATE/bug_report.md)

## 📝 Documentation Status

| Section | Status | Last Updated |
|---------|--------|--------------|
| Quick Start | ✅ Complete | 2024-01-15 |
| Installation | ✅ Complete | 2024-01-15 |
| Configuration | ✅ Complete | 2024-01-15 |
| Elasticsearch | ✅ Complete | 2024-01-15 |
| MySQL | 🚧 In Progress | - |
| PostgreSQL | 🚧 In Progress | - |
| MongoDB | 🚧 In Progress | - |
| API Reference | ✅ Complete | 2024-01-15 |
| Deployment | ✅ Complete | 2024-01-15 |
| Troubleshooting | ✅ Complete | 2024-01-15 |

---

**Need help?** Check our [troubleshooting guide](troubleshooting/common-issues.md) or [create an issue](https://github.com/PlanLX/planl-backup-kit/issues).