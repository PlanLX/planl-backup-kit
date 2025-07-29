"""Elasticsearch snapshot functionality."""

from datetime import datetime
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from models.config import SnapshotConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class ElasticsearchSnapshot:
    """Handles Elasticsearch snapshot operations to S3."""

    def __init__(self, config: SnapshotConfig):
        """Initialize snapshot handler with configuration."""
        self.config = config
        self.es_client: Elasticsearch | None = None

    async def connect(self) -> None:
        """Establish connection to Elasticsearch cluster."""
        try:
            # Build connection parameters
            connection_params = {
                "hosts": self.config.snapshot_hosts_list,
                "verify_certs": self.config.snapshot_verify_certs,
                "request_timeout": self.config.timeout,
            }

            # Add authentication if provided
            if self.config.snapshot_username and self.config.snapshot_password:
                connection_params.update(
                    {
                        "basic_auth": (
                            self.config.snapshot_username,
                            self.config.snapshot_password,
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

                logger.info(f"Creating S3 repository with settings: {settings}")
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

    async def create_snapshot(self) -> str:
        """Create snapshot of specified indices."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        # Generate snapshot name if not provided
        if not self.config.snapshot_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_name = f"snapshot_{timestamp}".lower()
        else:
            snapshot_name = self.config.snapshot_name.lower()

        try:
            # 简化快照配置，避免复杂参数
            snapshot_body = {
                "indices": ",".join(self.config.indices_list),
                "ignore_unavailable": True,
                "include_global_state": False,
                "partial": False,
            }

            logger.info(
                f"Creating snapshot '{snapshot_name}' for indices: {self.config.indices_list}"
            )

            # 先检查存储库状态
            try:
                repo_status = self.es_client.snapshot.get_repository(
                    name=self.config.repository_name
                )
                logger.info(f"Repository status: {repo_status}")
            except Exception as e:
                logger.warning(f"Could not get repository status: {e}")

            # 创建快照，不等待完成
            response = self.es_client.snapshot.create(
                repository=self.config.repository_name,
                snapshot=snapshot_name,
                body=snapshot_body,
                wait_for_completion=self.config.wait_for_completion,
                request_timeout=self.config.timeout,
            )

            logger.info(f"Snapshot '{snapshot_name}' started successfully")
            logger.info(f"Snapshot response: {response}")

            # 如果需要等待完成，则单独处理
            if self.config.wait_for_completion:
                logger.info("Waiting for snapshot completion...")
                # 这里可以添加轮询逻辑来检查快照状态
                # 暂时返回快照名称，让调用者处理等待逻辑

            return snapshot_name

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            # 添加更详细的错误信息
            if hasattr(e, "info"):
                logger.error(f"Error details: {e.info}")
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

    async def close(self) -> None:
        """Close Elasticsearch connection."""
        if self.es_client:
            self.es_client.close()
            logger.info("Closed Elasticsearch connection")

    async def list_snapshots(self) -> list:
        """List all snapshots in the repository."""
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

    async def delete_snapshot(self, snapshot_name: str) -> None:
        """Delete a specific snapshot."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        try:
            self.es_client.snapshot.delete(
                repository=self.config.repository_name, snapshot=snapshot_name
            )
            logger.info(f"Deleted snapshot: {snapshot_name}")
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_name}: {e}")
            raise

    async def cleanup_old_snapshots(self) -> None:
        """Clean up old snapshots based on retention settings."""
        if not self.config.retention_days and not self.config.retention_count:
            logger.info("No retention settings configured, skipping cleanup")
            return

        try:
            await self.connect()
            await self.create_repository()

            snapshots = await self.list_snapshots()
            if not snapshots:
                logger.info("No snapshots found, skipping cleanup")
                return

            # Sort snapshots by start time (newest first)
            snapshots.sort(key=lambda x: x.get("start_time") or "", reverse=True)

            snapshots_to_delete = []

            # Apply retention by count
            if (
                self.config.retention_count
                and len(snapshots) > self.config.retention_count
            ):
                # Keep the newest snapshots, mark older ones for deletion
                snapshots_to_delete.extend(
                    list(snapshots[self.config.retention_count :])
                )

            # Apply retention by days
            if self.config.retention_days:
                from datetime import datetime, timedelta

                cutoff_date = datetime.now() - timedelta(
                    days=self.config.retention_days
                )

                for snapshot in snapshots:
                    start_time_str = snapshot.get("start_time")
                    if not start_time_str:
                        continue

                    # Parse the start time (format: "2023-12-01T10:30:00.123Z")
                    try:
                        start_time = datetime.strptime(
                            start_time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S"
                        )

                        if start_time < cutoff_date:
                            # Only delete if not already marked for deletion
                            if snapshot not in snapshots_to_delete:
                                snapshots_to_delete.append(snapshot)
                    except ValueError:
                        logger.warning(
                            f"Could not parse start time for snapshot {snapshot.get('snapshot')}"
                        )

            # Remove duplicates while preserving order
            unique_snapshots_to_delete = []
            seen = set()
            for snapshot in snapshots_to_delete:
                snapshot_name = snapshot.get("snapshot")
                if snapshot_name not in seen:
                    seen.add(snapshot_name)
                    unique_snapshots_to_delete.append(snapshot)

            # Delete the snapshots
            for snapshot in unique_snapshots_to_delete:
                snapshot_name = snapshot.get("snapshot")
                try:
                    await self.delete_snapshot(snapshot_name)
                except Exception as e:
                    logger.error(f"Failed to delete snapshot {snapshot_name}: {e}")
                    # Continue with other deletions

            if unique_snapshots_to_delete:
                logger.info(
                    f"Cleaned up {len(unique_snapshots_to_delete)} old snapshots"
                )
            else:
                logger.info("No old snapshots to clean up")

        except Exception as e:
            logger.error(f"Failed to cleanup old snapshots: {e}")
            raise
        finally:
            await self.close()

    async def snapshot(self) -> str:
        """Perform complete snapshot operation."""
        try:
            await self.connect()
            await self.create_repository()
            snapshot_name = await self.create_snapshot()
            return snapshot_name

        finally:
            await self.close()
