#!/usr/bin/env python3
"""Elasticsearch Restore Tool

Elasticsearch restore tool designed for Kubernetes environments.
Reads configuration from environment variables and restores snapshots from S3.
"""

import asyncio
import os
import sys

from src.core.restore import ElasticsearchRestore
from src.models.config import SnapshotConfig
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


class RestoreManager:
    """Restore manager for Elasticsearch"""

    def __init__(self):
        """Initialize restore manager"""
        self.config = self._load_config_from_env()
        setup_logging(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "plain")
        )

    def _load_config_from_env(self) -> SnapshotConfig:
        """Load configuration from environment variables"""
        try:
            # Create config object, Pydantic will automatically read from environment variables
            config = SnapshotConfig()
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            raise

    async def restore_snapshot(self, snapshot_name: str) -> dict:
        """Restore snapshot"""
        try:
            logger.info("Starting snapshot restore", snapshot_name=snapshot_name)

            # Display restore information
            logger.info("Restore configuration",
                restore_cluster=self.config.restore_hosts_list,
                indices=self.config.indices_list,
                s3_bucket=self.config.bucket_name,
                repository=self.config.repository_name
            )

            # Create restore handler
            restore_handler = ElasticsearchRestore(self.config)
            
            # Connect to Elasticsearch
            await restore_handler.connect()
            
            # Create repository if needed
            await restore_handler.create_repository()
            
            # Check if snapshot exists
            if not await restore_handler.snapshot_exists(snapshot_name):
                raise ValueError(f"Snapshot '{snapshot_name}' does not exist")

            # Restore snapshot
            await restore_handler.restore(snapshot_name)

            logger.info("Snapshot restored successfully", snapshot_name=snapshot_name)
            
            # Close connection
            await restore_handler.close()
            
            return {
                "success": True,
                "snapshot_name": snapshot_name,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            logger.error("Failed to restore snapshot", 
                snapshot_name=snapshot_name,
                error=str(e)
            )
            raise

    async def list_snapshots(self) -> list:
        """List available snapshots"""
        try:
            logger.info("Listing available snapshots")

            # Create restore handler
            restore_handler = ElasticsearchRestore(self.config)
            
            # Connect to Elasticsearch
            await restore_handler.connect()
            
            # Create repository if needed
            await restore_handler.create_repository()
            
            # List snapshots
            snapshots = await restore_handler.list_snapshots()
            
            # Close connection
            await restore_handler.close()
            
            logger.info("Snapshots listed successfully", count=len(snapshots))
            return snapshots

        except Exception as e:
            logger.error("Failed to list snapshots", error=str(e))
            raise

    async def get_snapshot_status(self, snapshot_name: str) -> dict:
        """Get snapshot status"""
        try:
            logger.info("Getting snapshot status", snapshot_name=snapshot_name)

            # Create restore handler
            restore_handler = ElasticsearchRestore(self.config)
            
            # Connect to Elasticsearch
            await restore_handler.connect()
            
            # Create repository if needed
            await restore_handler.create_repository()
            
            # Get snapshot status
            status = await restore_handler.get_snapshot_status(snapshot_name)
            
            # Close connection
            await restore_handler.close()
            
            logger.info("Snapshot status retrieved successfully", 
                snapshot_name=snapshot_name,
                status=status.get('state', 'UNKNOWN')
            )
            return status

        except Exception as e:
            logger.error("Failed to get snapshot status", 
                snapshot_name=snapshot_name,
                error=str(e)
            )
            raise

    async def run_restore_workflow(self, snapshot_name: str) -> dict:
        """Execute complete restore workflow"""
        try:
            logger.info("Starting restore workflow", snapshot_name=snapshot_name)

            # Restore snapshot
            result = await self.restore_snapshot(snapshot_name)

            logger.info("Restore workflow completed successfully",
                snapshot_name=snapshot_name
            )
            return result

        except Exception as e:
            logger.error("Restore workflow failed", 
                snapshot_name=snapshot_name,
                error=str(e)
            )
            result = {
                "success": False,
                "error": str(e),
                "snapshot_name": snapshot_name,
                "timestamp": asyncio.get_event_loop().time(),
            }
            return result


async def main():
    """Main function"""
    try:
        # Check required environment variables
        required_env_vars = [
            "RESTORE_HOSTS",
            "ES_REPOSITORY_NAME",
            "ES_INDICES",
            "S3_BUCKET_NAME",
            "S3_REGION",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]

        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error("Missing required environment variables", missing_vars=missing_vars)
            sys.exit(1)

        # Get snapshot name from command line arguments or environment
        snapshot_name = os.getenv("SNAPSHOT_NAME")
        if not snapshot_name:
            if len(sys.argv) > 1:
                snapshot_name = sys.argv[1]
            else:
                logger.error("Snapshot name not provided. Use SNAPSHOT_NAME env var or command line argument")
                sys.exit(1)

        # Create restore manager
        manager = RestoreManager()

        # Execute restore workflow
        result = await manager.run_restore_workflow(snapshot_name)

        # Output result
        if result["success"]:
            logger.info(
                "Snapshot restored successfully",
                snapshot_name=result["snapshot_name"],
            )
            sys.exit(0)
        else:
            logger.error(
                "Restore failed",
                snapshot_name=result["snapshot_name"],
                error=result.get("error", "Unknown error"),
            )
            sys.exit(1)

    except Exception as e:
        logger.error("Program execution failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 