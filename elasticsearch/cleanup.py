#!/usr/bin/env python3
"""Elasticsearch Snapshot Cleanup Tool

Elasticsearch snapshot cleanup tool designed for Kubernetes environments.
Reads configuration from environment variables and cleans up expired snapshots.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List

from src.core.rotation import SnapshotRotation
from src.models.config import SnapshotConfig
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


class CleanupManager:
    """Cleanup manager for Elasticsearch snapshots"""

    def __init__(self):
        """Initialize cleanup manager"""
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

    async def cleanup_snapshots(
        self,
        snapshot_names: List[str] = None,
        all_snapshots: bool = False,
        pattern: str = None,
        older_than: str = None,
        dry_run: bool = False
    ) -> dict:
        """Clean up snapshots based on specified criteria"""
        try:
            logger.info("Starting snapshot cleanup")
            
            # Display cleanup information
            logger.info("Cleanup configuration",
                snapshot_names=snapshot_names,
                all_snapshots=all_snapshots,
                pattern=pattern,
                older_than=older_than,
                dry_run=dry_run
            )

            # Create rotation handler
            rotation_handler = SnapshotRotation(self.config)
            await rotation_handler.connect()
            await rotation_handler.create_repository()

            # Get all snapshots
            all_snapshots_list = await rotation_handler.list_snapshots()
            if not all_snapshots_list:
                logger.info("No snapshots found in repository")
                return {"success": True, "deleted": [], "message": "No snapshots found"}

            # Determine snapshots to delete
            snapshots_to_delete = []

            if all_snapshots:
                # Delete all snapshots
                snapshots_to_delete = [s.get("snapshot", "") for s in all_snapshots_list]
                logger.info(f"Will delete all {len(snapshots_to_delete)} snapshots")

            elif snapshot_names:
                # Delete specified snapshots
                existing_snapshots = [s.get("snapshot", "") for s in all_snapshots_list]
                for name in snapshot_names:
                    if name in existing_snapshots:
                        snapshots_to_delete.append(name)
                    else:
                        logger.warning(f"Snapshot '{name}' does not exist")
                        
            elif pattern:
                # Delete snapshots matching pattern
                import re
                existing_snapshots = [s.get("snapshot", "") for s in all_snapshots_list]
                try:
                    pattern_regex = re.compile(pattern.replace("*", ".*"))
                    for snapshot in existing_snapshots:
                        if pattern_regex.match(snapshot):
                            snapshots_to_delete.append(snapshot)
                except re.error as e:
                    logger.error(f"Invalid pattern '{pattern}': {e}")
                    raise ValueError(f"Invalid pattern: {e}")

            elif older_than:
                # Delete snapshots older than specified date
                try:
                    cutoff_date = datetime.strptime(older_than, "%Y-%m-%d")
                    for snapshot in all_snapshots_list:
                        snapshot_name = snapshot.get("snapshot", "")
                        snapshot_date = rotation_handler.parse_snapshot_date(
                            snapshot_name
                        )
                        if snapshot_date and snapshot_date.date() < cutoff_date.date():
                            snapshots_to_delete.append(snapshot_name)
                except ValueError as e:
                    logger.error(f"Invalid date format '{older_than}': {e}")
                    raise ValueError(f"Invalid date format: {e}")

            if not snapshots_to_delete:
                logger.info("No snapshots to delete")
                return {"success": True, "deleted": [], "message": "No snapshots to delete"}

            # Perform cleanup
            deleted_snapshots = []
            failed_snapshots = []

            if dry_run:
                logger.info(f"Dry run: would delete {len(snapshots_to_delete)} snapshots")
                return {
                    "success": True,
                    "deleted": snapshots_to_delete,
                    "failed": [],
                    "dry_run": True,
                    "message": f"Would delete {len(snapshots_to_delete)} snapshots"
                }

            for snapshot_name in snapshots_to_delete:
                try:
                    await rotation_handler.delete_snapshot(snapshot_name)
                    deleted_snapshots.append(snapshot_name)
                    logger.info(f"Successfully deleted snapshot: {snapshot_name}")
                except Exception as e:
                    failed_snapshots.append({"name": snapshot_name, "error": str(e)})
                    logger.error(f"Failed to delete snapshot '{snapshot_name}': {e}")

            logger.info("Snapshot cleanup completed",
                deleted_count=len(deleted_snapshots),
                failed_count=len(failed_snapshots)
            )
            
            return {
                "success": True,
                "deleted": deleted_snapshots,
                "failed": failed_snapshots,
                "message": f"Deleted {len(deleted_snapshots)} snapshots, failed {len(failed_snapshots)}"
            }

        except Exception as e:
            logger.error("Failed to cleanup snapshots", error=str(e))
            raise
        finally:
            await rotation_handler.close()

    async def run_cleanup(
        self,
        snapshot_names: List[str] = None,
        all_snapshots: bool = False,
        pattern: str = None,
        older_than: str = None,
        dry_run: bool = False
    ) -> dict:
        """Execute complete cleanup workflow"""
        try:
            logger.info("Starting cleanup workflow")

            # Execute cleanup
            result = await self.cleanup_snapshots(
                snapshot_names=snapshot_names,
                all_snapshots=all_snapshots,
                pattern=pattern,
                older_than=older_than,
                dry_run=dry_run
            )

            logger.info("Cleanup workflow completed successfully",
                deleted_count=len(result.get("deleted", [])),
                failed_count=len(result.get("failed", []))
            )
            return result

        except Exception as e:
            logger.error("Cleanup workflow failed", error=str(e))
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
            "S3_BUCKET_NAME",
            "S3_REGION",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]

        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error("Missing required environment variables", missing_vars=missing_vars)
            sys.exit(1)

        # Create cleanup manager
        manager = CleanupManager()

        # For now, we'll do a basic cleanup with default parameters
        # In a more complete implementation, we would parse command line arguments
        result = await manager.run_cleanup()

        # Log results
        if result["success"]:
            logger.info(
                "Cleanup completed successfully",
                deleted_count=len(result.get("deleted", [])),
                message=result.get("message", "")
            )
            sys.exit(0)
        else:
            logger.error(
                "Cleanup failed",
                error=result.get("error", "Unknown error"),
            )
            sys.exit(1)

    except Exception as e:
        logger.error("Program execution failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())