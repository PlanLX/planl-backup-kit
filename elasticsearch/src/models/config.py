"""Configuration models for Elasticsearch snapshot and restore operations."""


from pydantic import Field, validator
from pydantic_settings import BaseSettings


class SnapshotConfig(BaseSettings):
    """Main configuration for snapshot and restore operations."""

    # Elasticsearch configuration
    snapshot_hosts: str = Field(
        ..., description="Snapshot Elasticsearch hosts", alias="SNAPSHOT_HOSTS"
    )
    snapshot_username: str | None = Field(
        None, description="Snapshot cluster username", alias="SNAPSHOT_USERNAME"
    )
    snapshot_password: str | None = Field(
        None, description="Snapshot cluster password", alias="SNAPSHOT_PASSWORD"
    )
    snapshot_verify_certs: bool = Field(
        True,
        description="Verify SSL certificates for snapshot cluster",
        alias="SNAPSHOT_VERIFY_CERTS",
    )

    restore_hosts: str = Field(
        ..., description="Restore Elasticsearch hosts", alias="RESTORE_HOSTS"
    )
    restore_username: str | None = Field(
        None, description="Restore cluster username", alias="RESTORE_USERNAME"
    )
    restore_password: str | None = Field(
        None, description="Restore cluster password", alias="RESTORE_PASSWORD"
    )
    restore_verify_certs: bool = Field(
        True,
        description="Verify SSL certificates for restore cluster",
        alias="RESTORE_VERIFY_CERTS",
    )

    repository_name: str = Field(
        ..., description="S3 repository name", alias="ES_REPOSITORY_NAME"
    )
    snapshot_name: str | None = Field(
        None,
        description="Snapshot name (auto-generated if not provided)",
        alias="ES_SNAPSHOT_NAME",
    )
    indices: str = Field(
        ..., description="List of indices to snapshot/restore", alias="ES_INDICES"
    )

    # S3 configuration
    bucket_name: str = Field(..., description="S3 bucket name", alias="S3_BUCKET_NAME")
    base_path: str = Field(
        default="elasticsearch-snapshots",
        description="Base path in S3 bucket",
        alias="S3_BASE_PATH",
    )
    region: str = Field(..., description="AWS region", alias="S3_REGION")
    endpoint: str | None = Field(
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

    # AWS region (if different from S3 region)
    aws_region: str | None = Field(
        None, description="AWS region (if different from S3 region)", alias="AWS_REGION"
    )

    # Operation settings
    wait_for_completion: bool = Field(
        True, description="Wait for snapshot/restore completion"
    )
    timeout: int = Field(300, description="Operation timeout in seconds")

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

    @property
    def snapshot_hosts_list(self) -> list[str]:
        """Get snapshot hosts as a list."""
        if "," not in self.snapshot_hosts:
            return [self.snapshot_hosts.strip()]
        return [host.strip() for host in self.snapshot_hosts.split(",")]

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

    @validator("snapshot_hosts", "restore_hosts")
    def validate_hosts(cls, v):
        """Validate that at least one host is provided."""
        if not v or not v.strip():
            raise ValueError("At least one host must be provided")
        return v

    @validator("indices")
    def validate_indices(cls, v):
        """Validate that at least one index is specified."""
        if not v or not v.strip():
            raise ValueError("At least one index must be specified")
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False
