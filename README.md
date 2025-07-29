# PlanLX Backup Kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

A comprehensive backup toolkit for various databases and services, designed for production environments with Kubernetes support.

## 🚀 Features

- **Multi-Database Support**: Elasticsearch, MySQL, PostgreSQL, MongoDB
- **Cloud Storage Integration**: AWS S3, Azure Blob Storage, Google Cloud Storage
- **Kubernetes Ready**: Native K8s support with CronJob examples
- **Automated Rotation**: Intelligent snapshot rotation and cleanup
- **Security First**: Secure credential management and encryption
- **Production Grade**: Built for reliability and scalability
- **Easy Deployment**: Docker containers and Helm charts included

## 📦 Quick Start

### Prerequisites

- Python 3.12+
- Docker (for containerized deployment)
- Kubernetes cluster (for K8s deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/PlanLX/planl-backup-kit.git
cd planl-backup-kit

# Install dependencies for a specific service
cd elasticsearch
uv sync
```

### Basic Usage

```bash
# Elasticsearch backup
cd elasticsearch
python main.py --config .env snapshot

# List available snapshots
python main.py list-snapshots

# Rotate old snapshots
python main.py rotate --max-snapshots 10 --max-age-days 30
```

## 🏗️ Architecture

```
planl-backup-kit/
├── elasticsearch/          # Elasticsearch backup tools
│   ├── src/               # Source code
│   ├── Dockerfile         # Container image
│   ├── docker-compose.yml # Local development
│   └── example/           # K8s deployment examples
├── mysql/                 # MySQL backup tools (coming soon)
├── postgresql/            # PostgreSQL backup tools (coming soon)
├── mongodb/               # MongoDB backup tools (coming soon)
├── .github/               # GitHub Actions workflows
└── docs/                  # Documentation
```

## 🔧 Configuration

### Environment Variables

```bash
# Elasticsearch Configuration
SNAPSHOT_HOSTS=http://elasticsearch:9200
ES_REPOSITORY_NAME=s3_backup
ES_INDICES=*

# S3 Configuration
S3_BUCKET_NAME=my-backup-bucket
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Rotation Settings
MAX_SNAPSHOTS=10
MAX_AGE_DAYS=30
KEEP_SUCCESSFUL_ONLY=true
```

### Configuration Files

Each service supports multiple configuration formats:

- **Environment Variables**: For containerized deployments
- **YAML/JSON**: For complex configurations
- **Command Line**: For quick operations

## 🐳 Docker Deployment

### Local Development

```bash
# Start Elasticsearch and Kibana
cd elasticsearch
docker-compose up -d

# Run backup
docker run --rm \
  -e SNAPSHOT_HOSTS=http://elasticsearch:9200 \
  -e S3_BUCKET_NAME=my-bucket \
  planlx/elasticsearch-backup-kit:latest
```

### Kubernetes Deployment

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: elasticsearch-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: planlx/elasticsearch-backup-kit:latest
            env:
            - name: SNAPSHOT_HOSTS
              value: "http://elasticsearch:9200"
            - name: S3_BUCKET_NAME
              value: "my-backup-bucket"
          restartPolicy: OnFailure
```

## 🚀 CI/CD Pipeline

### GitHub Actions

The project includes automated CI/CD pipelines:

- **Build & Test**: On every push and PR
- **Docker Images**: Automated builds for multiple environments
- **Security Scanning**: Trivy vulnerability scanning
- **Deployment**: Automated deployment to staging/production

### Local Development

```bash
# Run tests
uv run pytest

# Code formatting
uv run ruff format .
uv run ruff check .

# Type checking
uv run mypy src/
```

## 📚 Documentation

- [Elasticsearch Backup Guide](elasticsearch/README.md)
- [Kubernetes Deployment](elasticsearch/example/)
- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/planl-backup-kit.git
cd planl-backup-kit

# Install development dependencies
cd elasticsearch
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run ruff format .
```

### Code Style

- **Python**: Black + Ruff + MyPy
- **YAML**: Prettier
- **Documentation**: Markdown linting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/PlanLX/planl-backup-kit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PlanLX/planl-backup-kit/discussions)
- **Email**: sloudy@gmail.com

## 🙏 Acknowledgments

- [Elasticsearch](https://www.elastic.co/) for the excellent search engine
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## 📊 Project Status

| Service | Status | Version | Tests |
|---------|--------|---------|-------|
| Elasticsearch | ✅ Production Ready | 0.1.0 | [![Tests](https://github.com/PlanLX/planl-backup-kit/workflows/Tests/badge.svg)](https://github.com/PlanLX/planl-backup-kit/actions) |
| MySQL | 🚧 In Development | - | - |
| PostgreSQL | 🚧 In Development | - | - |
| MongoDB | 🚧 In Development | - | - |

---

**Made with ❤️ by the PlanLX Team**