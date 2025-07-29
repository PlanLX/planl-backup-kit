#!/usr/bin/env python3
"""K8s Elasticsearch Snapshot and Cleanup Tool

Elasticsearch snapshot and cleanup tool designed for Kubernetes environments.
Reads configuration from environment variables, creates snapshots and automatically cleans up expired snapshots.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for developmen
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from core.rotation import SnapshotRotation
from core.snapshot import ElasticsearchSnapshot
from models.config import SnapshotConfig
from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


class SnapshotManager:
    """Snapshot manager for K8s environment"""

    def __init__(self):
        """Initialize snapshot manager"""
        self.config = self._load_config_from_env()
        setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

    def _load_config_from_env(self) -> SnapshotConfig:
        """Load configuration from environment variables"""
        try:
            # Create config object, Pydantic will automatically read from environment variables
            config = SnapshotConfig()
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    async def create_snapshot(self) -> str:
        """Create snapshot"""
        try:
            logger.info("Starting snapshot creation...")

            # Display snapshot information
            logger.info(f"Snapshot cluster: {self.config.snapshot_hosts_list}")
            logger.info(f"Indices: {self.config.indices_list}")
            logger.info(f"S3 bucket: {self.config.bucket_name}")
            logger.info(f"Repository: {self.config.repository_name}")

            # Create snapshot
            snapshot_handler = ElasticsearchSnapshot(self.config)
            snapshot_name = await snapshot_handler.snapshot()

            logger.info(f"Snapshot created successfully: {snapshot_name}")
            return snapshot_name

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise

    async def cleanup_old_snapshots(self) -> dict:
        """Clean up expired snapshots"""
        try:
            logger.info("Starting cleanup of expired snapshots...")

            # Display cleanup strategy
            logger.info(f"Max snapshots to keep: {self.config.max_snapshots}")
            logger.info(f"Max age in days: {self.config.max_age_days}")
            logger.info(
                f"Keep successful snapshots only: {self.config.keep_successful_only}"
            )

            # Execute rotation cleanup
            rotation_handler = SnapshotRotation(self.config)
            result = await rotation_handler.rotate(
                max_snapshots=self.config.max_snapshots,
                max_age_days=self.config.max_age_days,
                keep_successful_only=self.config.keep_successful_only,
            )

            logger.info(
                f"Snapshot cleanup completed: deleted {result['total_deleted']}, kept {result['total_kept']}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to cleanup snapshots: {e}")
            raise

    async def run_snapshot_and_cleanup(self) -> dict:
        """Execute complete snapshot creation and cleanup workflow"""
        try:
            logger.info("Starting snapshot and cleanup workflow...")

            # 1. Create snapshot
            snapshot_name = await self.create_snapshot()

            # 2. Cleanup expired snapshots
            cleanup_result = await self.cleanup_old_snapshots()

            # 3. Return result
            result = {
                "success": True,
                "snapshot_name": snapshot_name,
                "cleanup_result": cleanup_result,
                "timestamp": asyncio.get_event_loop().time(),
            }

            logger.info("Snapshot and cleanup workflow completed successfully")
            return result

        except Exception as e:
            logger.error(f"Snapshot and cleanup workflow failed: {e}")
            result = {
                "success": False,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            }
            return result


async def main():
    """Main function"""
    try:
        # Check required environment variables
        required_env_vars = [
            "SNAPSHOT_HOSTS",
            "ES_REPOSITORY_NAME",
            "ES_INDICES",
            "S3_BUCKET_NAME",
            "S3_REGION",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]

        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            sys.exit(1)

        # Create snapshot manager
        manager = SnapshotManager()

        # Execute snapshot and cleanup workflow
        result = await manager.run_snapshot_and_cleanup()

        # Output result
        if result["success"]:
            print(f"SUCCESS: Snapshot {result['snapshot_name']} created successfully")
            print(
                f"Cleanup result: Deleted {result['cleanup_result']['total_deleted']} snapshots"
            )
            sys.exit(0)
        else:
            print(f"ERROR: {result['error']}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Program execution failed: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
