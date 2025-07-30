"""Elasticsearch snapshot rotation functionality."""

from datetime import datetime, timedelta
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from src.models.config import SnapshotConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SnapshotRotation:
    """Handles Elasticsearch snapshot rotation and cleanup operations."""

    def __init__(self, config: SnapshotConfig):
        """Initialize rotation handler with configuration."""
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

    async def delete_snapshot(self, snapshot_name: str) -> None:
        """Delete a specific snapshot."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        try:
            logger.info(f"Deleting snapshot: {snapshot_name}")
            self.es_client.snapshot.delete(
                repository=self.config.repository_name,
                snapshot=snapshot_name,
                request_timeout=self.config.timeout,
            )
            logger.info(f"Successfully deleted snapshot: {snapshot_name}")

        except NotFoundError:
            logger.warning(f"Snapshot '{snapshot_name}' not found")
        except Exception as e:
            logger.error(f"Failed to delete snapshot '{snapshot_name}': {e}")
            raise

    def parse_snapshot_date(self, snapshot_name: str) -> datetime | None:
        """Parse date from snapshot name."""
        try:
            # 支持多种快照命名格式
            if snapshot_name.startswith("snapshot_"):
                # 格式: snapshot_2025_07_29t13_04_24
                date_str = snapshot_name.replace("snapshot_", "").replace("t", "T")
                # 修复下划线格式
                date_str = date_str.replace("_", "-")
                return datetime.fromisoformat(date_str)
            elif snapshot_name.startswith("snapshot"):
                # 格式: snapshot20250729_131212
                date_str = snapshot_name.replace("snapshot", "")
                if "_" in date_str:
                    date_part, time_part = date_str.split("_", 1)
                    # 假设格式为 YYYYMMDD_HHMMSS
                    if len(date_part) == 8 and len(time_part) == 6:
                        return datetime.strptime(
                            f"{date_part}_{time_part}", "%Y%m%d_%H%M%S"
                        )
            return None
        except Exception as e:
            logger.warning(
                f"Could not parse date from snapshot name '{snapshot_name}': {e}"
            )
            return None

    async def rotate_snapshots(
        self,
        max_snapshots: int = 10,
        max_age_days: int = 30,
        keep_successful_only: bool = True,
    ) -> dict[str, Any]:
        """Rotate snapshots based on retention policy."""
        if not self.es_client:
            raise RuntimeError("Not connected to Elasticsearch")

        try:
            snapshots = await self.list_snapshots()
            if not snapshots:
                logger.info("No snapshots found for rotation")
                return {"deleted": [], "kept": [], "total_deleted": 0}

            # 过滤快照
            valid_snapshots = []
            for snapshot in snapshots:
                snapshot_name = snapshot.get("snapshot", "")
                state = snapshot.get("state", "")

                # 只保留成功的快照（如果指定）
                if keep_successful_only and state != "SUCCESS":
                    logger.info(
                        f"Skipping failed snapshot: {snapshot_name} (state: {state})"
                    )
                    continue

                # 解析快照日期
                snapshot_date = self.parse_snapshot_date(snapshot_name)
                if snapshot_date is None:
                    logger.warning(
                        f"Could not parse date for snapshot: {snapshot_name}"
                    )
                    continue

                valid_snapshots.append(
                    {
                        "name": snapshot_name,
                        "date": snapshot_date,
                        "state": state,
                        "original": snapshot,
                    }
                )

            # 按日期排序（最新的在前）
            valid_snapshots.sort(key=lambda x: x["date"], reverse=True)

            # 应用保留策略
            snapshots_to_delete = []
            snapshots_to_keep = []

            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            for i, snapshot in enumerate(valid_snapshots):
                should_delete = False
                reason = ""

                # 检查数量限制
                if i >= max_snapshots:
                    should_delete = True
                    reason = f"Exceeds max_snapshots limit ({max_snapshots})"

                # 检查年龄限制
                elif snapshot["date"] < cutoff_date:
                    should_delete = True
                    reason = f"Older than {max_age_days} days"

                if should_delete:
                    snapshots_to_delete.append(
                        {
                            "name": snapshot["name"],
                            "date": snapshot["date"],
                            "reason": reason,
                        }
                    )
                else:
                    snapshots_to_keep.append(
                        {
                            "name": snapshot["name"],
                            "date": snapshot["date"],
                        }
                    )

            # 删除过期的快照
            deleted_snapshots = []
            for snapshot in snapshots_to_delete:
                try:
                    await self.delete_snapshot(snapshot["name"])
                    deleted_snapshots.append(snapshot)
                except Exception as e:
                    logger.error(f"Failed to delete snapshot {snapshot['name']}: {e}")

            result = {
                "deleted": deleted_snapshots,
                "kept": snapshots_to_keep,
                "total_deleted": len(deleted_snapshots),
                "total_kept": len(snapshots_to_keep),
                "policy": {
                    "max_snapshots": max_snapshots,
                    "max_age_days": max_age_days,
                    "keep_successful_only": keep_successful_only,
                },
            }

            logger.info(
                f"Rotation completed: {len(deleted_snapshots)} deleted, {len(snapshots_to_keep)} kept"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to rotate snapshots: {e}")
            raise

    async def close(self) -> None:
        """Close Elasticsearch connection."""
        if self.es_client:
            self.es_client.close()
            logger.info("Closed Elasticsearch connection")

    async def rotate(self, **kwargs) -> dict[str, Any]:
        """Perform complete rotation operation."""
        try:
            await self.connect()
            await self.create_repository()
            result = await self.rotate_snapshots(**kwargs)
            return result

        finally:
            await self.close()
