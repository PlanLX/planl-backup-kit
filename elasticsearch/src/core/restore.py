"""Elasticsearch restore functionality."""

from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from models.config import SnapshotConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class ElasticsearchRestore:
    """Handles Elasticsearch restore operations from S3."""

    def __init__(self, config: SnapshotConfig):
        """Initialize restore handler with configuration."""
        self.config = config
        self.es_client: Elasticsearch | None = None

    async def connect(self) -> None:
        """Establish connection to Elasticsearch cluster."""
        try:
            # Build connection parameters
            connection_params = {
                "hosts": self.config.restore_hosts_list,
                "verify_certs": self.config.restore_verify_certs,
                "request_timeout": self.config.timeout,
            }

            # Add authentication if provided
            if self.config.restore_username and self.config.restore_password:
                connection_params.update(
                    {
                        "basic_auth": (
                            self.config.restore_username,
                            self.config.restore_password,
                        )
                    }
                )

            self.es_client = Elasticsearch(**connection_params)

            # Test connection
            info = self.es_client.info()
            logger.info(f"Connected to Elasticsearch cluster: {info['cluster_name']}")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    async def create_repository(self) -> None:
        """Create repository for snapshots."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        try:
            # 根据存储库名称判断类型
            if self.config.repository_name.startswith("s3_"):
                settings = {
                    "bucket": self.config.bucket_name,
                    "base_path": self.config.base_path,
                    "region": self.config.region,
                }

                # Add optional settings if they are provided
                if self.config.endpoint:
                    settings["endpoint"] = self.config.endpoint

                if self.config.protocol:
                    settings["protocol"] = self.config.protocol
                if self.config.path_style_access is not None:
                    settings["path_style_access"] = self.config.path_style_access
                if hasattr(self.config, "aws_region") and self.config.aws_region:
                    settings["region"] = self.config.aws_region

                repository_body = {
                    "type": "s3",
                    "settings": settings,
                }
            else:
                # 默认使用文件系统存储库
                repository_body = {
                    "type": "fs",
                    "settings": {
                        "location": f"/usr/share/elasticsearch/data/snapshots/{self.config.repository_name}",
                        "compress": True,
                    },
                }

            self.es_client.snapshot.create_repository(
                name=self.config.repository_name,
                body=repository_body,
                request_timeout=self.config.timeout,
                verify=False,
            )

            logger.info(f"Created repository: {self.config.repository_name}")

        except RequestError as e:
            if "already exists" in str(e):
                logger.info(f"Repository already exists: {self.config.repository_name}")
            else:
                logger.error(f"Failed to create repository: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating repository: {e}")
            raise

    async def close_indices(self, indices: list[str]) -> None:
        """Close indices before restore operation."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        for index in indices:
            try:
                logger.info(f"Closing index: {index}")
                self.es_client.indices.close(
                    index=index,
                    ignore_unavailable=True,
                    request_timeout=self.config.timeout,
                )
            except NotFoundError:
                logger.warning(f"Index '{index}' not found - skipping close operation")
            except Exception as e:
                logger.error(f"Failed to close index '{index}': {e}")
                raise

    async def open_indices(self, indices: list[str]) -> None:
        """Open indices after restore operation."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        for index in indices:
            try:
                logger.info(f"Opening index: {index}")
                self.es_client.indices.open(
                    index=index,
                    ignore_unavailable=True,
                    request_timeout=self.config.timeout,
                )
            except NotFoundError:
                logger.warning(f"Index '{index}' not found - skipping open operation")
            except Exception as e:
                logger.error(f"Failed to open index '{index}': {e}")
                raise

    async def restore_snapshot(self, snapshot_name: str) -> None:
        """Restore snapshot to destination cluster."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        if not snapshot_name:
            raise ValueError("Snapshot name is required for restore operation")

        try:
            restore_body = {
                "indices": ",".join(self.config.indices_list),
                "ignore_unavailable": True,
                "include_global_state": False,
                "include_aliases": True,
            }

            logger.info(
                f"Restoring snapshot '{snapshot_name}' for indices: {self.config.indices_list}"
            )

            # Close indices before restore
            await self.close_indices(self.config.indices_list)

            # Perform restore
            self.es_client.snapshot.restore(
                repository=self.config.repository_name,
                snapshot=snapshot_name,
                body=restore_body,
                wait_for_completion=self.config.wait_for_completion,
                request_timeout=self.config.timeout,
            )

            if self.config.wait_for_completion:
                logger.info(
                    f"Restore from snapshot '{snapshot_name}' completed successfully"
                )
            else:
                logger.info(
                    f"Restore from snapshot '{snapshot_name}' started successfully"
                )

            # Open indices after restore
            await self.open_indices(self.config.indices_list)

        except Exception as e:
            logger.error(f"Failed to restore snapshot: {e}")
            # Try to reopen indices even if restore failed
            try:
                await self.open_indices(self.config.indices_list)
            except Exception as reopen_error:
                logger.error(
                    f"Failed to reopen indices after restore failure: {reopen_error}"
                )
            raise

    async def get_snapshot_status(self, snapshot_name: str) -> dict[str, Any]:
        """Get status of a snapshot."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        try:
            response = self.es_client.snapshot.get(
                repository=self.config.repository_name,
                snapshot=snapshot_name,
            )

            return response

        except NotFoundError:
            logger.warning(f"Snapshot '{snapshot_name}' not found")
            return {}
        except Exception as e:
            logger.error(f"Failed to get snapshot status: {e}")
            raise

    async def list_snapshots(self) -> list[dict[str, Any]]:
        """List all available snapshots in the repository."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        try:
            response = self.es_client.snapshot.get(
                repository=self.config.repository_name, snapshot="_all"
            )

            return response.get("snapshots", [])

        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            raise

    async def close(self) -> None:
        """Close Elasticsearch connection."""
        if self.es_client:
            self.es_client.close()
            logger.info("Closed Elasticsearch connection")

    async def restore(self, snapshot_name: str) -> None:
        """Perform complete restore operation."""
        try:
            await self.connect()
            await self.create_repository()
            await self.restore_snapshot(snapshot_name)

        finally:
            await self.close()
