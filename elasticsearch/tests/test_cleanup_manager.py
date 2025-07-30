#!/usr/bin/env python3
"""Test CleanupManager functionality following TDD methodology."""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
from datetime import datetime

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from cleanup import CleanupManager


class TestCleanupManager:
    """Test cases for CleanupManager class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.snapshot_hosts_list = ["http://localhost:9200"]
        config.indices_list = ["test_index"]
        config.bucket_name = "test-bucket"
        config.repository_name = "test-repo"
        config.max_snapshots = 10
        config.max_age_days = 30
        config.keep_successful_only = True
        return config

    @pytest.fixture
    def cleanup_manager(self, mock_config):
        """Create CleanupManager instance with mocked config."""
        with patch('cleanup.SnapshotConfig', return_value=mock_config):
            with patch('cleanup.setup_logging'):
                manager = CleanupManager()
                return manager

    @pytest.mark.asyncio
    async def test_cleanup_manager_initialization(self, cleanup_manager):
        """Test CleanupManager initialization."""
        # Arrange & Act
        manager = cleanup_manager
        
        # Assert
        assert manager is not None
        assert hasattr(manager, 'config')
        assert hasattr(manager, '_load_config_from_env')

    @pytest.mark.asyncio
    async def test_cleanup_snapshots_all_success(self, cleanup_manager):
        """Test successful cleanup of all snapshots."""
        # Arrange
        mock_snapshots = [
            {"snapshot": "snapshot_1", "state": "SUCCESS"},
            {"snapshot": "snapshot_2", "state": "SUCCESS"}
        ]
        mock_rotation_handler = AsyncMock()
        mock_rotation_handler.list_snapshots = AsyncMock(return_value=mock_snapshots)
        mock_rotation_handler.delete_snapshot = AsyncMock()
        mock_rotation_handler.parse_snapshot_date = Mock(return_value=datetime.now())
        mock_rotation_handler.connect = AsyncMock()
        mock_rotation_handler.create_repository = AsyncMock()
        mock_rotation_handler.close = AsyncMock()
        
        with patch('cleanup.SnapshotRotation', return_value=mock_rotation_handler):
            # Act
            result = await cleanup_manager.cleanup_snapshots(all_snapshots=True)
            
            # Assert
            assert result["success"] is True
            assert len(result["deleted"]) == 2
            assert mock_rotation_handler.delete_snapshot.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_snapshots_by_name_success(self, cleanup_manager):
        """Test successful cleanup of snapshots by name."""
        # Arrange
        mock_snapshots = [
            {"snapshot": "snapshot_1", "state": "SUCCESS"},
            {"snapshot": "snapshot_2", "state": "SUCCESS"},
            {"snapshot": "snapshot_3", "state": "SUCCESS"}
        ]
        mock_rotation_handler = AsyncMock()
        mock_rotation_handler.list_snapshots = AsyncMock(return_value=mock_snapshots)
        mock_rotation_handler.delete_snapshot = AsyncMock()
        mock_rotation_handler.connect = AsyncMock()
        mock_rotation_handler.create_repository = AsyncMock()
        mock_rotation_handler.close = AsyncMock()
        
        with patch('cleanup.SnapshotRotation', return_value=mock_rotation_handler):
            # Act
            result = await cleanup_manager.cleanup_snapshots(snapshot_names=["snapshot_1", "snapshot_3"])
            
            # Assert
            assert result["success"] is True
            assert len(result["deleted"]) == 2
            assert "snapshot_1" in result["deleted"]
            assert "snapshot_3" in result["deleted"]
            assert mock_rotation_handler.delete_snapshot.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_snapshots_by_pattern_success(self, cleanup_manager):
        """Test successful cleanup of snapshots by pattern."""
        # Arrange
        mock_snapshots = [
            {"snapshot": "snapshot_2025_07_29", "state": "SUCCESS"},
            {"snapshot": "snapshot_2025_07_30", "state": "SUCCESS"},
            {"snapshot": "backup_2025_07_30", "state": "SUCCESS"}
        ]
        mock_rotation_handler = AsyncMock()
        mock_rotation_handler.list_snapshots = AsyncMock(return_value=mock_snapshots)
        mock_rotation_handler.delete_snapshot = AsyncMock()
        mock_rotation_handler.connect = AsyncMock()
        mock_rotation_handler.create_repository = AsyncMock()
        mock_rotation_handler.close = AsyncMock()
        
        with patch('cleanup.SnapshotRotation', return_value=mock_rotation_handler):
            # Act
            result = await cleanup_manager.cleanup_snapshots(pattern="snapshot_*")
            
            # Assert
            assert result["success"] is True
            assert len(result["deleted"]) == 2
            assert mock_rotation_handler.delete_snapshot.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_snapshots_older_than_success(self, cleanup_manager):
        """Test successful cleanup of snapshots older than date."""
        # Arrange
        mock_snapshots = [
            {"snapshot": "snapshot_2025_07_29", "state": "SUCCESS"},
            {"snapshot": "snapshot_2025_07_30", "state": "SUCCESS"}
        ]
        mock_rotation_handler = AsyncMock()
        mock_rotation_handler.list_snapshots = AsyncMock(return_value=mock_snapshots)
        mock_rotation_handler.delete_snapshot = AsyncMock()
        # Mock parse_snapshot_date to return different dates for different snapshots
        def parse_date_mock(snapshot_name):
            if snapshot_name == "snapshot_2025_07_29":
                return datetime(2025, 7, 29)
            elif snapshot_name == "snapshot_2025_07_30":
                return datetime(2025, 7, 30)
            return None
        mock_rotation_handler.parse_snapshot_date = Mock(side_effect=parse_date_mock)
        mock_rotation_handler.connect = AsyncMock()
        mock_rotation_handler.create_repository = AsyncMock()
        mock_rotation_handler.close = AsyncMock()
        
        with patch('cleanup.SnapshotRotation', return_value=mock_rotation_handler):
            # Act
            result = await cleanup_manager.cleanup_snapshots(older_than="2025-07-30")
            
            # Assert
            assert result["success"] is True
            assert len(result["deleted"]) == 1
            assert mock_rotation_handler.delete_snapshot.call_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_snapshots_dry_run(self, cleanup_manager):
        """Test dry run mode for cleanup."""
        # Arrange
        mock_snapshots = [
            {"snapshot": "snapshot_1", "state": "SUCCESS"},
            {"snapshot": "snapshot_2", "state": "SUCCESS"}
        ]
        mock_rotation_handler = AsyncMock()
        mock_rotation_handler.list_snapshots = AsyncMock(return_value=mock_snapshots)
        mock_rotation_handler.connect = AsyncMock()
        mock_rotation_handler.create_repository = AsyncMock()
        mock_rotation_handler.close = AsyncMock()
        
        with patch('cleanup.SnapshotRotation', return_value=mock_rotation_handler):
            # Act
            result = await cleanup_manager.cleanup_snapshots(all_snapshots=True, dry_run=True)
            
            # Assert
            assert result["success"] is True
            assert result["dry_run"] is True
            assert len(result["deleted"]) == 2
            # Verify no actual deletions occurred
            assert mock_rotation_handler.delete_snapshot.call_count == 0

    @pytest.mark.asyncio
    async def test_cleanup_snapshots_failure(self, cleanup_manager):
        """Test cleanup failure handling."""
        # Arrange
        mock_rotation_handler = AsyncMock()
        mock_rotation_handler.list_snapshots = AsyncMock(side_effect=Exception("Connection failed"))
        mock_rotation_handler.connect = AsyncMock()
        mock_rotation_handler.create_repository = AsyncMock()
        mock_rotation_handler.close = AsyncMock()
        
        with patch('cleanup.SnapshotRotation', return_value=mock_rotation_handler):
            # Act & Assert
            with pytest.raises(Exception, match="Connection failed"):
                await cleanup_manager.cleanup_snapshots(all_snapshots=True)

    @pytest.mark.asyncio
    async def test_run_cleanup_success(self, cleanup_manager):
        """Test successful cleanup workflow."""
        # Arrange
        expected_result = {
            "success": True,
            "deleted": ["snapshot_1", "snapshot_2"],
            "message": "Deleted 2 snapshots"
        }
        
        with patch.object(cleanup_manager, 'cleanup_snapshots', return_value=expected_result):
            # Act
            result = await cleanup_manager.run_cleanup(all_snapshots=True)
            
            # Assert
            assert result == expected_result
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_run_cleanup_failure(self, cleanup_manager):
        """Test cleanup workflow failure."""
        # Arrange
        error_message = "Connection failed"
        
        with patch.object(cleanup_manager, 'cleanup_snapshots', side_effect=Exception(error_message)):
            # Act
            result = await cleanup_manager.run_cleanup(all_snapshots=True)
            
            # Assert
            assert result["success"] is False
            assert result["error"] == error_message
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_load_config_from_env_success(self, cleanup_manager):
        """Test successful configuration loading from environment."""
        # Arrange
        os.environ.update({
            "SNAPSHOT_HOSTS": "http://localhost:9200",
            "ES_REPOSITORY_NAME": "test-repo",
            "ES_INDICES": "test_index",
            "S3_BUCKET_NAME": "test-bucket",
            "S3_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "plain"
        })
        
        try:
            # Act
            config = cleanup_manager._load_config_from_env()
            
            # Assert
            assert config is not None
            
        finally:
            # Cleanup
            for key in ["SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
                       "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
                       "AWS_SECRET_ACCESS_KEY", "LOG_LEVEL", "LOG_FORMAT"]:
                os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_load_config_from_env_missing_vars(self, cleanup_manager):
        """Test configuration loading failure when required variables are missing."""
        # Arrange - Clear all environment variables
        env_vars_to_clear = [
            "SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "S3_BUCKET_NAME", 
            "S3_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)
        
        # Act & Assert
        with pytest.raises(Exception):
            cleanup_manager._load_config_from_env()


class TestCleanupManagerIntegration:
    """Integration tests for CleanupManager."""

    @pytest.mark.asyncio
    async def test_cleanup_manager_with_real_config(self):
        """Test CleanupManager with real configuration loading."""
        # Arrange
        os.environ.update({
            "SNAPSHOT_HOSTS": "http://localhost:9200",
            "ES_REPOSITORY_NAME": "test-repo",
            "ES_INDICES": "test_index",
            "S3_BUCKET_NAME": "test-bucket",
            "S3_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "plain"
        })
        
        try:
            # Act
            manager = CleanupManager()
            
            # Assert
            assert manager is not None
            assert manager.config is not None
            assert manager.config.snapshot_hosts_list == ["http://localhost:9200"]
            assert manager.config.indices_list == ["test_index"]
            assert manager.config.bucket_name == "test-bucket"
            assert manager.config.repository_name == "test-repo"
            
        finally:
            # Cleanup
            for key in ["SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
                       "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
                       "AWS_SECRET_ACCESS_KEY", "LOG_LEVEL", "LOG_FORMAT"]:
                os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_cleanup_manager_configuration_validation(self):
        """Test configuration validation with various scenarios."""
        # Test cases for different configuration scenarios
        test_cases = [
            {
                "name": "valid_config",
                "env_vars": {
                    "SNAPSHOT_HOSTS": "http://localhost:9200",
                    "ES_REPOSITORY_NAME": "test-repo",
                    "ES_INDICES": "test_index",
                    "S3_BUCKET_NAME": "test-bucket",
                    "S3_REGION": "us-east-1",
                    "AWS_ACCESS_KEY_ID": "test-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret"
                },
                "should_succeed": True
            },
            {
                "name": "missing_snapshot_hosts",
                "env_vars": {
                    "ES_REPOSITORY_NAME": "test-repo",
                    "ES_INDICES": "test_index",
                    "S3_BUCKET_NAME": "test-bucket",
                    "S3_REGION": "us-east-1",
                    "AWS_ACCESS_KEY_ID": "test-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret"
                },
                "should_succeed": False
            },
            {
                "name": "missing_s3_bucket",
                "env_vars": {
                    "SNAPSHOT_HOSTS": "http://localhost:9200",
                    "ES_REPOSITORY_NAME": "test-repo",
                    "ES_INDICES": "test_index",
                    "S3_REGION": "us-east-1",
                    "AWS_ACCESS_KEY_ID": "test-key",
                    "AWS_SECRET_ACCESS_KEY": "test-secret"
                },
                "should_succeed": False
            }
        ]
        
        for test_case in test_cases:
            # Arrange
            for key, value in test_case["env_vars"].items():
                os.environ[key] = value
            
            try:
                # Act & Assert
                if test_case["should_succeed"]:
                    manager = CleanupManager()
                    assert manager.config is not None
                    print(f"✓ {test_case['name']} passed")
                else:
                    with pytest.raises(Exception):
                        CleanupManager()
                    print(f"✓ {test_case['name']} correctly failed")
                    
            finally:
                # Cleanup
                for key in test_case["env_vars"]:
                    os.environ.pop(key, None)


if __name__ == "__main__":
    # Run tests without coverage for local testing
    pytest.main([__file__, "-v", "--no-cov"])