#!/usr/bin/env python3
"""Test RestoreManager functionality following TDD methodology."""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from restore import RestoreManager


class TestRestoreManager:
    """Test cases for RestoreManager class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.restore_hosts_list = ["http://localhost:9200"]
        config.indices_list = ["test_index"]
        config.bucket_name = "test-bucket"
        config.repository_name = "test-repo"
        config.max_snapshots = 10
        config.max_age_days = 30
        config.keep_successful_only = True
        return config

    @pytest.fixture
    def restore_manager(self, mock_config):
        """Create RestoreManager instance with mocked config."""
        with patch('restore.SnapshotConfig', return_value=mock_config):
            with patch('restore.setup_logging'):
                manager = RestoreManager()
                return manager

    @pytest.mark.asyncio
    async def test_restore_manager_initialization(self, restore_manager):
        """Test RestoreManager initialization."""
        # Arrange & Act
        manager = restore_manager
        
        # Assert
        assert manager is not None
        assert hasattr(manager, 'config')
        assert hasattr(manager, '_load_config_from_env')

    @pytest.mark.asyncio
    async def test_restore_snapshot_success(self, restore_manager):
        """Test successful snapshot restore."""
        # Arrange
        snapshot_name = "test_snapshot_20250730_120000"
        mock_restore_handler = Mock()
        mock_restore_handler.connect = AsyncMock()
        mock_restore_handler.create_repository = AsyncMock()
        mock_restore_handler.snapshot_exists = AsyncMock(return_value=True)
        mock_restore_handler.restore = AsyncMock()
        mock_restore_handler.close = AsyncMock()
        
        with patch('restore.ElasticsearchRestore', return_value=mock_restore_handler):
            # Act
            result = await restore_manager.restore_snapshot(snapshot_name)
            
            # Assert
            assert result["success"] is True
            assert result["snapshot_name"] == snapshot_name
            assert "timestamp" in result
            mock_restore_handler.connect.assert_called_once()
            mock_restore_handler.create_repository.assert_called_once()
            mock_restore_handler.snapshot_exists.assert_called_once_with(snapshot_name)
            mock_restore_handler.restore.assert_called_once_with(snapshot_name)
            mock_restore_handler.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_snapshot_not_exists(self, restore_manager):
        """Test restore when snapshot does not exist."""
        # Arrange
        snapshot_name = "non_existent_snapshot"
        mock_restore_handler = Mock()
        mock_restore_handler.connect = AsyncMock()
        mock_restore_handler.create_repository = AsyncMock()
        mock_restore_handler.snapshot_exists = AsyncMock(return_value=False)
        mock_restore_handler.close = AsyncMock()
        
        with patch('restore.ElasticsearchRestore', return_value=mock_restore_handler):
            # Act & Assert
            with pytest.raises(ValueError, match=f"Snapshot '{snapshot_name}' does not exist"):
                await restore_manager.restore_snapshot(snapshot_name)
            
            mock_restore_handler.connect.assert_called_once()
            mock_restore_handler.create_repository.assert_called_once()
            mock_restore_handler.snapshot_exists.assert_called_once_with(snapshot_name)
            # Note: close() is not called when snapshot doesn't exist due to early exception

    @pytest.mark.asyncio
    async def test_list_snapshots_success(self, restore_manager):
        """Test successful listing of snapshots."""
        # Arrange
        mock_snapshots = [
            {"snapshot": "snapshot_1", "state": "SUCCESS"},
            {"snapshot": "snapshot_2", "state": "SUCCESS"}
        ]
        mock_restore_handler = Mock()
        mock_restore_handler.connect = AsyncMock()
        mock_restore_handler.create_repository = AsyncMock()
        mock_restore_handler.list_snapshots = AsyncMock(return_value=mock_snapshots)
        mock_restore_handler.close = AsyncMock()
        
        with patch('restore.ElasticsearchRestore', return_value=mock_restore_handler):
            # Act
            result = await restore_manager.list_snapshots()
            
            # Assert
            assert result == mock_snapshots
            assert len(result) == 2
            mock_restore_handler.connect.assert_called_once()
            mock_restore_handler.create_repository.assert_called_once()
            mock_restore_handler.list_snapshots.assert_called_once()
            mock_restore_handler.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_snapshot_status_success(self, restore_manager):
        """Test successful getting of snapshot status."""
        # Arrange
        snapshot_name = "test_snapshot"
        mock_status = {
            "snapshot": snapshot_name,
            "state": "SUCCESS",
            "start_time": "2025-07-30T12:00:00Z",
            "end_time": "2025-07-30T12:05:00Z"
        }
        mock_restore_handler = Mock()
        mock_restore_handler.connect = AsyncMock()
        mock_restore_handler.create_repository = AsyncMock()
        mock_restore_handler.get_snapshot_status = AsyncMock(return_value=mock_status)
        mock_restore_handler.close = AsyncMock()
        
        with patch('restore.ElasticsearchRestore', return_value=mock_restore_handler):
            # Act
            result = await restore_manager.get_snapshot_status(snapshot_name)
            
            # Assert
            assert result == mock_status
            assert result["state"] == "SUCCESS"
            mock_restore_handler.connect.assert_called_once()
            mock_restore_handler.create_repository.assert_called_once()
            mock_restore_handler.get_snapshot_status.assert_called_once_with(snapshot_name)
            mock_restore_handler.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_restore_workflow_success(self, restore_manager):
        """Test successful restore workflow."""
        # Arrange
        snapshot_name = "test_snapshot"
        expected_result = {
            "success": True,
            "snapshot_name": snapshot_name,
            "timestamp": 1234567890.0
        }
        
        with patch.object(restore_manager, 'restore_snapshot', return_value=expected_result):
            # Act
            result = await restore_manager.run_restore_workflow(snapshot_name)
            
            # Assert
            assert result == expected_result
            assert result["success"] is True
            assert result["snapshot_name"] == snapshot_name

    @pytest.mark.asyncio
    async def test_run_restore_workflow_failure(self, restore_manager):
        """Test restore workflow failure."""
        # Arrange
        snapshot_name = "test_snapshot"
        error_message = "Connection failed"
        
        with patch.object(restore_manager, 'restore_snapshot', side_effect=Exception(error_message)):
            # Act
            result = await restore_manager.run_restore_workflow(snapshot_name)
            
            # Assert
            assert result["success"] is False
            assert result["snapshot_name"] == snapshot_name
            assert result["error"] == error_message
            assert "timestamp" in result


class TestRestoreManagerIntegration:
    """Integration tests for RestoreManager."""

    @pytest.mark.asyncio
    async def test_restore_manager_with_real_config(self):
        """Test RestoreManager with real configuration loading."""
        # Arrange
        os.environ.update({
            "SNAPSHOT_HOSTS": "http://localhost:9200",  # Required by SnapshotConfig
            "RESTORE_HOSTS": "http://localhost:9200",
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
            manager = RestoreManager()
            
            # Assert
            assert manager is not None
            assert manager.config is not None
            assert manager.config.snapshot_hosts_list == ["http://localhost:9200"]
            assert manager.config.indices_list == ["test_index"]
            assert manager.config.bucket_name == "test-bucket"
            
        finally:
            # Cleanup
            for key in ["SNAPSHOT_HOSTS", "RESTORE_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
                       "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
                       "AWS_SECRET_ACCESS_KEY", "LOG_LEVEL", "LOG_FORMAT"]:
                os.environ.pop(key, None)


if __name__ == "__main__":
    # Run tests without coverage for local testing
    pytest.main([__file__, "-v", "--no-cov"]) 