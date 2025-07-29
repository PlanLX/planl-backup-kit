# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Elasticsearch backup and restore functionality
- S3 repository support
- Snapshot rotation and cleanup features
- Kubernetes deployment examples
- Docker containerization
- GitHub Actions CI/CD pipeline

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - 2024-01-15

### Added
- **Elasticsearch Backup Kit**: Complete backup and restore solution
  - Snapshot creation with S3 storage
  - Snapshot restoration functionality
  - Snapshot listing and status monitoring
  - Automated snapshot rotation and cleanup
  - Kubernetes CronJob support
  - Docker containerization
  - Comprehensive CLI interface

- **Core Features**:
  - Multi-environment support (k8s, dev, prod)
  - Environment variable configuration
  - YAML/JSON configuration files
  - Asynchronous operations
  - Rich terminal output
  - Comprehensive error handling
  - Logging and monitoring

- **Infrastructure**:
  - GitHub Actions workflows
  - Docker image builds
  - Security scanning with Trivy
  - Automated testing
  - Code quality checks

- **Documentation**:
  - Comprehensive README
  - API documentation
  - Deployment guides
  - Troubleshooting guides
  - Contributing guidelines

### Technical Details
- **Python 3.12+** support
- **FastAPI** for web framework
- **Pydantic** for data validation
- **Click** for CLI interface
- **Rich** for terminal output
- **Elasticsearch** Python client
- **Boto3** for AWS S3 integration
- **UV** for dependency management
- **Ruff** for code formatting and linting
- **MyPy** for type checking

---

## Version History

- **0.1.0**: Initial release with Elasticsearch backup functionality

## Release Notes

### Version 0.1.0
This is the initial release of PlanLX Backup Kit, focusing on Elasticsearch backup and restore capabilities. The release includes:

- Complete Elasticsearch snapshot management
- S3 storage integration
- Kubernetes deployment support
- Production-ready Docker containers
- Comprehensive documentation

### Future Releases
- MySQL backup support
- PostgreSQL backup support
- MongoDB backup support
- Additional cloud storage providers
- Advanced monitoring and alerting
- Web-based management interface

---

For detailed information about each release, please refer to the [GitHub releases page](https://github.com/PlanLX/planl-backup-kit/releases).