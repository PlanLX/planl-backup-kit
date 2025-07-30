"""Configuration models for Elasticsearch snapshot and restore operations."""

from enum import Enum
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class OperationMode(str, Enum):
    """Operation mode enumeration."""

    SNAPSHOT = "snapshot"
    RESTORE = "restore"
    BOTH = "both"


class BaseElasticsearchConfig(BaseSettings):
    """Base configuration for Elasticsearch operations."""

    # Common Elasticsearch configuration
    hosts: str = Field(..., description="Elasticsearch hosts")
    username: Optional[str] = Field(None, description="Elasticsearch username")
    password: Optional[str] = Field(None, description="Elasticsearch password")
    verify_certs: bool = Field(True, description="Verify SSL certificates")
    timeout: int = Field(300, description="Operation timeout in seconds")

    @property
    def hosts_list(self) -> list[str]:
        """Get hosts as a list."""
        if "," not in self.hosts:
            return [self.hosts.strip()]
        return [host.strip() for host in self.hosts.split(",")]

    @field_validator("hosts")
    @classmethod
    def validate_hosts(cls, v):
        """Validate that at least one host is provided."""
        if not v or not v.strip():
            raise ValueError("At least one host must be provided")
        return v


class SnapshotConfig(BaseSettings):
    """Configuration for snapshot operations."""

    # Operation mode
    operation_mode: OperationMode = Field(
        default=OperationMode.SNAPSHOT,
        description="Operation mode",
        alias="OPERATION_MODE",
    )

    # Snapshot-specific configuration
    snapshot_hosts: str = Field(
        ..., description="Snapshot Elasticsearch hosts", alias="SNAPSHOT_HOSTS"
    )
    snapshot_username: Optional[str] = Field(
        None, description="Snapshot cluster username", alias="SNAPSHOT_USERNAME"
    )
    snapshot_password: Optional[str] = Field(
        None, description="Snapshot cluster password", alias="SNAPSHOT_PASSWORD"
    )
    snapshot_verify_certs: bool = Field(
        True,
        description="Verify SSL certificates for snapshot cluster",
        alias="SNAPSHOT_VERIFY_CERTS",
    )

    # Repository and snapshot configuration
    repository_name: str = Field(
        ..., description="S3 repository name", alias="ES_REPOSITORY_NAME"
    )
    snapshot_name: Optional[str] = Field(
        None,
        description="Snapshot name (auto-generated if not provided)",
        alias="ES_SNAPSHOT_NAME",
    )
    indices: str = Field(
        ..., description="List of indices to snapshot", alias="ES_INDICES"
    )
    wait_for_completion: bool = Field(
        True, description="Wait for snapshot completion", alias="ES_WAIT_FOR_COMPLETION"
    )
    timeout: int = Field(
        300, description="Operation timeout in seconds", alias="SNAPSHOT_TIMEOUT"
    )

    # S3 configuration
    bucket_name: str = Field(..., description="S3 bucket name", alias="S3_BUCKET_NAME")
    base_path: str = Field(
        default="elasticsearch-snapshots",
        description="Base path in S3 bucket",
        alias="S3_BASE_PATH",
    )
    region: str = Field(..., description="AWS region", alias="S3_REGION")
    endpoint: Optional[str] = Field(
        None,
        description="S3 endpoint URL (for custom S3-compatible services)",
        alias="S3_ENDPOINT",
    )
    protocol: str = Field(
        default="https", description="S3 protocol (http or https)", alias="S3_PROTOCOL"
    )
    path_style_access: bool = Field(
        default=True,
        description="Use path-style access for S3",
        alias="S3_PATH_STYLE_ACCESS",
    )
    compress: bool = Field(
        default=True,
        description="Compress snapshots",
        alias="S3_COMPRESS",
    )

    # AWS credentials
    access_key: str = Field(
        ..., description="AWS access key ID", alias="AWS_ACCESS_KEY_ID"
    )
    secret_key: str = Field(
        ..., description="AWS secret access key", alias="AWS_SECRET_ACCESS_KEY"
    )

    # AWS region (if different from S3 region)
    aws_region: Optional[str] = Field(
        None, description="AWS region (if different from S3 region)", alias="AWS_REGION"
    )

    # Rotation settings
    max_snapshots: int = Field(
        default=10,
        description="Maximum number of snapshots to keep",
        alias="MAX_SNAPSHOTS",
    )
    max_age_days: int = Field(
        default=30, description="Maximum age of snapshots in days", alias="MAX_AGE_DAYS"
    )
    keep_successful_only: bool = Field(
        default=True,
        description="Keep only successful snapshots",
        alias="KEEP_SUCCESSFUL_ONLY",
    )
    enable_rotation: bool = Field(
        default=False,
        description="Enable automatic snapshot rotation",
        alias="ENABLE_ROTATION",
    )
    cleanup_old_snapshots: bool = Field(
        default=True,
        description="Clean up old snapshots",
        alias="CLEANUP_OLD_SNAPSHOTS",
    )
    snapshot_retention_days: int = Field(
        default=30,
        description="Snapshot retention days",
        alias="SNAPSHOT_RETENTION_DAYS",
    )

    # Backward compatibility fields
    retention_days: int = Field(
        default=30,
        description="Retention days (backward compatibility)",
        alias="RETENTION_DAYS",
    )
    retention_count: int = Field(
        default=10,
        description="Retention count (backward compatibility)",
        alias="RETENTION_COUNT",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Log level",
        alias="LOG_LEVEL",
    )
    log_format: str = Field(
        default="json",
        description="Log format",
        alias="LOG_FORMAT",
    )

    # Health check configuration
    health_check_enabled: bool = Field(
        default=True,
        description="Enable health checks",
        alias="HEALTH_CHECK_ENABLED",
    )
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds",
        alias="HEALTH_CHECK_INTERVAL",
    )

    @property
    def snapshot_hosts_list(self) -> list[str]:
        """Get snapshot hosts as a list."""
        if "," not in self.snapshot_hosts:
            return [self.snapshot_hosts.strip()]
        return [host.strip() for host in self.snapshot_hosts.split(",")]

    @property
    def indices_list(self) -> list[str]:
        """Get indices as a list."""
        if "," not in self.indices:
            return [self.indices.strip()]
        return [index.strip() for index in self.indices.split(",")]

    @field_validator("snapshot_hosts")
    @classmethod
    def validate_snapshot_hosts(cls, v):
        """Validate that at least one snapshot host is provided."""
        if not v or not v.strip():
            raise ValueError("At least one snapshot host must be provided")
        return v

    @field_validator("indices")
    @classmethod
    def validate_indices(cls, v):
        """Validate that at least one index is specified."""
        if not v or not v.strip():
            raise ValueError("At least one index must be specified")
        return v

    @field_validator("repository_name")
    @classmethod
    def validate_repository_name(cls, v):
        """Validate repository name."""
        if not v or not v.strip():
            raise ValueError("Repository name must be specified")
        return v

    @field_validator("bucket_name")
    @classmethod
    def validate_bucket_name(cls, v):
        """Validate S3 bucket name."""
        if not v or not v.strip():
            raise ValueError("S3 bucket name must be specified")
        return v

    @field_validator("access_key")
    @classmethod
    def validate_access_key(cls, v):
        """Validate AWS access key."""
        if not v or not v.strip():
            raise ValueError("AWS access key must be specified")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate AWS secret key."""
        if not v or not v.strip():
            raise ValueError("AWS secret key must be specified")
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False


class RestoreConfig(BaseSettings):
    """Configuration for restore operations."""

    # Operation mode
    operation_mode: OperationMode = Field(
        default=OperationMode.RESTORE,
        description="Operation mode",
        alias="OPERATION_MODE",
    )

    # Restore-specific configuration
    restore_hosts: str = Field(
        ..., description="Restore Elasticsearch hosts", alias="RESTORE_HOSTS"
    )
    restore_username: Optional[str] = Field(
        None, description="Restore cluster username", alias="RESTORE_USERNAME"
    )
    restore_password: Optional[str] = Field(
        None, description="Restore cluster password", alias="RESTORE_PASSWORD"
    )
    restore_verify_certs: bool = Field(
        True,
        description="Verify SSL certificates for restore cluster",
        alias="RESTORE_VERIFY_CERTS",
    )

    # Repository and snapshot configuration
    repository_name: str = Field(
        ..., description="S3 repository name", alias="ES_REPOSITORY_NAME"
    )
    snapshot_name: str = Field(
        ..., description="Snapshot name to restore", alias="ES_SNAPSHOT_NAME"
    )
    indices: str = Field(
        ..., description="List of indices to restore", alias="ES_INDICES"
    )
    wait_for_completion: bool = Field(
        True, description="Wait for restore completion", alias="ES_WAIT_FOR_COMPLETION"
    )

    # S3 configuration (same as snapshot)
    bucket_name: str = Field(..., description="S3 bucket name", alias="S3_BUCKET_NAME")
    base_path: str = Field(
        default="elasticsearch-snapshots",
        description="Base path in S3 bucket",
        alias="S3_BASE_PATH",
    )
    region: str = Field(..., description="AWS region", alias="S3_REGION")
    endpoint: Optional[str] = Field(
        None,
        description="S3 endpoint URL (for custom S3-compatible services)",
        alias="S3_ENDPOINT",
    )
    protocol: str = Field(
        default="https", description="S3 protocol (http or https)", alias="S3_PROTOCOL"
    )
    path_style_access: bool = Field(
        default=True,
        description="Use path-style access for S3",
        alias="S3_PATH_STYLE_ACCESS",
    )

    # AWS credentials
    access_key: str = Field(
        ..., description="AWS access key ID", alias="AWS_ACCESS_KEY_ID"
    )
    secret_key: str = Field(
        ..., description="AWS secret access key", alias="AWS_SECRET_ACCESS_KEY"
    )

    # Restore-specific settings
    rename_pattern: Optional[str] = Field(
        None,
        description="Pattern to rename indices during restore",
        alias="RESTORE_RENAME_PATTERN",
    )
    rename_replacement: Optional[str] = Field(
        None,
        description="Replacement for renamed indices",
        alias="RESTORE_RENAME_REPLACEMENT",
    )
    ignore_unavailable: bool = Field(
        default=True,
        description="Ignore unavailable indices during restore",
        alias="RESTORE_IGNORE_UNAVAILABLE",
    )
    partial: bool = Field(
        default=False,
        description="Allow partial restore",
        alias="RESTORE_PARTIAL",
    )

    @property
    def restore_hosts_list(self) -> list[str]:
        """Get restore hosts as a list."""
        if "," not in self.restore_hosts:
            return [self.restore_hosts.strip()]
        return [host.strip() for host in self.restore_hosts.split(",")]

    @property
    def indices_list(self) -> list[str]:
        """Get indices as a list."""
        if "," not in self.indices:
            return [self.indices.strip()]
        return [index.strip() for index in self.indices.split(",")]

    @field_validator("restore_hosts")
    @classmethod
    def validate_restore_hosts(cls, v):
        """Validate that at least one restore host is provided."""
        if not v or not v.strip():
            raise ValueError("At least one restore host must be provided")
        return v

    @field_validator("snapshot_name")
    @classmethod
    def validate_snapshot_name(cls, v):
        """Validate snapshot name is provided for restore."""
        if not v or not v.strip():
            raise ValueError("Snapshot name must be specified for restore operations")
        return v

    @field_validator("indices")
    @classmethod
    def validate_indices(cls, v):
        """Validate that at least one index is specified."""
        if not v or not v.strip():
            raise ValueError("At least one index must be specified")
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False
