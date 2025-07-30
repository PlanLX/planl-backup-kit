#!/usr/bin/env python3
"""Test SnapshotManager functionality following TDD methodology."""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from snapshot import SnapshotManager


class TestSnapshotManager:
    """Test cases for SnapshotManager class."""

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
    def snapshot_manager(self, mock_config):
        """Create SnapshotManager instance with mocked config."""
        with patch('snapshot.SnapshotConfig', return_value=mock_config):
            with patch('snapshot.setup_logging'):
                manager = SnapshotManager()
                return manager

    @pytest.mark.asyncio
    async def test_snapshot_manager_initialization(self, snapshot_manager):
        """Test SnapshotManager initialization."""
        # Arrange & Act
        manager = snapshot_manager
        
        # Assert
        assert manager is not None
        assert hasattr(manager, 'config')
        assert hasattr(manager, '_load_config_from_env')

    @pytest.mark.asyncio
    async def test_snapshot_manager_initialization_with_real_config(self):
        """Test SnapshotManager initialization with real configuration."""
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
            manager = SnapshotManager()
            
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
    async def test_create_snapshot_success(self, snapshot_manager):
        """Test successful snapshot creation."""
        # Arrange
        expected_snapshot_name = "snapshot_20250730_120000"
        mock_snapshot_handler = Mock()
        mock_snapshot_handler.snapshot = AsyncMock(return_value=expected_snapshot_name)
        
        with patch('snapshot.ElasticsearchSnapshot', return_value=mock_snapshot_handler):
            # Act
            result = await snapshot_manager.create_snapshot()
            
            # Assert
            assert result == expected_snapshot_name
            mock_snapshot_handler.snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_with_config_logging(self, snapshot_manager):
        """Test snapshot creation with configuration logging."""
        # Arrange
        expected_snapshot_name = "snapshot_20250730_120000"
        mock_snapshot_handler = Mock()
        mock_snapshot_handler.snapshot = AsyncMock(return_value=expected_snapshot_name)
        
        with patch('snapshot.ElasticsearchSnapshot', return_value=mock_snapshot_handler):
            # Act
            result = await snapshot_manager.create_snapshot()
            
            # Assert
            assert result == expected_snapshot_name
            mock_snapshot_handler.snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_with_different_config(self):
        """Test snapshot creation with different configuration values."""
        # Arrange
        mock_config = Mock()
        mock_config.snapshot_hosts_list = ["http://es1:9200", "http://es2:9200"]
        mock_config.indices_list = ["index1", "index2", "index3"]
        mock_config.bucket_name = "production-backups"
        mock_config.repository_name = "prod-repo"
        mock_config.max_snapshots = 10
        mock_config.max_age_days = 30
        mock_config.keep_successful_only = True
        
        with patch('snapshot.SnapshotConfig', return_value=mock_config):
            with patch('snapshot.setup_logging'):
                manager = SnapshotManager()
                
                expected_snapshot_name = "snapshot_20250730_150000"
                mock_snapshot_handler = Mock()
                mock_snapshot_handler.snapshot = AsyncMock(return_value=expected_snapshot_name)
                
                with patch('snapshot.ElasticsearchSnapshot', return_value=mock_snapshot_handler):
                    # Act
                    result = await manager.create_snapshot()
                    
                    # Assert
                    assert result == expected_snapshot_name
                    mock_snapshot_handler.snapshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_failure(self, snapshot_manager):
        """Test snapshot creation failure."""
        # Arrange
        error_message = "Connection failed"
        mock_snapshot_handler = Mock()
        mock_snapshot_handler.snapshot = AsyncMock(side_effect=Exception(error_message))
        
        with patch('snapshot.ElasticsearchSnapshot', return_value=mock_snapshot_handler):
            # Act & Assert
            with pytest.raises(Exception, match=error_message):
                await snapshot_manager.create_snapshot()

    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots_success(self, snapshot_manager):
        """Test successful cleanup of old snapshots."""
        # Arrange
        expected_cleanup_result = {
            "total_deleted": 2,
            "total_kept": 5
        }
        mock_rotation_handler = Mock()
        mock_rotation_handler.rotate = AsyncMock(return_value=expected_cleanup_result)
        
        with patch('snapshot.SnapshotRotation', return_value=mock_rotation_handler):
            # Act
            result = await snapshot_manager.cleanup_old_snapshots()
            
            # Assert
            assert result == expected_cleanup_result
            mock_rotation_handler.rotate.assert_called_once_with(
                max_snapshots=snapshot_manager.config.max_snapshots,
                max_age_days=snapshot_manager.config.max_age_days,
                keep_successful_only=snapshot_manager.config.keep_successful_only
            )

    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots_with_custom_config(self):
        """Test cleanup of old snapshots with custom configuration values."""
        # Arrange
        mock_config = Mock()
        mock_config.snapshot_hosts_list = ["http://localhost:9200"]
        mock_config.indices_list = ["test_index"]
        mock_config.bucket_name = "test-bucket"
        mock_config.repository_name = "test-repo"
        mock_config.max_snapshots = 5
        mock_config.max_age_days = 15
        mock_config.keep_successful_only = False
        
        with patch('snapshot.SnapshotConfig', return_value=mock_config):
            with patch('snapshot.setup_logging'):
                manager = SnapshotManager()
                
                expected_cleanup_result = {
                    "total_deleted": 1,
                    "total_kept": 3
                }
                mock_rotation_handler = Mock()
                mock_rotation_handler.rotate = AsyncMock(return_value=expected_cleanup_result)
                
                with patch('snapshot.SnapshotRotation', return_value=mock_rotation_handler):
                    # Act
                    result = await manager.cleanup_old_snapshots()
                    
                    # Assert
                    assert result == expected_cleanup_result
                    mock_rotation_handler.rotate.assert_called_once_with(
                        max_snapshots=5,
                        max_age_days=15,
                        keep_successful_only=False
                    )

    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots_failure(self, snapshot_manager):
        """Test cleanup failure."""
        # Arrange
        error_message = "Repository not found"
        mock_rotation_handler = Mock()
        mock_rotation_handler.rotate = AsyncMock(side_effect=Exception(error_message))
        
        with patch('snapshot.SnapshotRotation', return_value=mock_rotation_handler):
            # Act & Assert
            with pytest.raises(Exception, match=error_message):
                await snapshot_manager.cleanup_old_snapshots()

    @pytest.mark.asyncio
    async def test_run_snapshot_and_cleanup_success(self, snapshot_manager):
        """Test successful snapshot and cleanup workflow."""
        # Arrange
        expected_snapshot_name = "snapshot_20250730_120000"
        expected_cleanup_result = {
            "total_deleted": 2,
            "total_kept": 5
        }
        
        with patch.object(snapshot_manager, 'create_snapshot', return_value=expected_snapshot_name):
            with patch.object(snapshot_manager, 'cleanup_old_snapshots', return_value=expected_cleanup_result):
                # Act
                result = await snapshot_manager.run_snapshot_and_cleanup()
                
                # Assert
        assert result["success"] is True
        assert result["snapshot_name"] == expected_snapshot_name
        assert result["cleanup_result"] == expected_cleanup_result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_run_snapshot_and_cleanup_with_different_results(self):
        """Test snapshot and cleanup workflow with different results."""
        # Arrange
        mock_config = Mock()
        mock_config.snapshot_hosts_list = ["http://localhost:9200"]
        mock_config.indices_list = ["test_index"]
        mock_config.bucket_name = "test-bucket"
        mock_config.repository_name = "test-repo"
        mock_config.max_snapshots = 10
        mock_config.max_age_days = 30
        mock_config.keep_successful_only = True
        
        with patch('snapshot.SnapshotConfig', return_value=mock_config):
            with patch('snapshot.setup_logging'):
                manager = SnapshotManager()
                
                expected_snapshot_name = "daily-snapshot-2025-07-30"
                expected_cleanup_result = {
                    "total_deleted": 0,
                    "total_kept": 8
                }
                
                with patch.object(manager, 'create_snapshot', return_value=expected_snapshot_name):
                    with patch.object(manager, 'cleanup_old_snapshots', return_value=expected_cleanup_result):
                        # Act
                        result = await manager.run_snapshot_and_cleanup()
                        
                        # Assert
                        assert result["success"] is True
                        assert result["snapshot_name"] == expected_snapshot_name
                        assert result["cleanup_result"] == expected_cleanup_result
                        assert "timestamp" in result
        
    @pytest.mark.asyncio
    async def test_run_snapshot_and_cleanup_snapshot_failure(self, snapshot_manager):
        """Test workflow failure when snapshot creation fails."""
        # Arrange
        error_message = "Snapshot creation failed"
        
        with patch.object(snapshot_manager, 'create_snapshot', side_effect=Exception(error_message)):
            # Act
            result = await snapshot_manager.run_snapshot_and_cleanup()
            
            # Assert
            assert result["success"] is False
            assert result["error"] == error_message
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_run_snapshot_and_cleanup_cleanup_failure(self, snapshot_manager):
        """Test workflow failure when cleanup fails."""
        # Arrange
        expected_snapshot_name = "snapshot_20250730_120000"
        error_message = "Cleanup failed"
        
        with patch.object(snapshot_manager, 'create_snapshot', return_value=expected_snapshot_name):
            with patch.object(snapshot_manager, 'cleanup_old_snapshots', side_effect=Exception(error_message)):
                # Act
                result = await snapshot_manager.run_snapshot_and_cleanup()
                
                # Assert
        assert result["success"] is False
        assert result["error"] == error_message
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_load_config_from_env_success(self, snapshot_manager):
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
            config = snapshot_manager._load_config_from_env()
            
            # Assert
            assert config is not None
            assert config.snapshot_hosts_list == ["http://localhost:9200"]
            assert config.indices_list == ["test_index"]
            assert config.bucket_name == "test-bucket"
            assert config.repository_name == "test-repo"
            
        finally:
            # Cleanup
            for key in ["SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
                       "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
                       "AWS_SECRET_ACCESS_KEY", "LOG_LEVEL", "LOG_FORMAT"]:
                os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_load_config_from_env_missing_vars(self, snapshot_manager):
        """Test configuration loading failure when required variables are missing."""
        # Arrange - Clear all environment variables
        env_vars_to_clear = [
            "SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
            "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
            "AWS_SECRET_ACCESS_KEY"
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)
        
        # Act & Assert
        with pytest.raises(Exception):
            snapshot_manager._load_config_from_env()

    @pytest.mark.asyncio
    async def test_snapshot_config_properties(self):
        """Test SnapshotConfig properties."""
        # Arrange
        os.environ.update({
            "SNAPSHOT_HOSTS": "http://localhost:9200,http://localhost:9201",
            "ES_REPOSITORY_NAME": "test-repo",
            "ES_INDICES": "index1,index2,index3",
            "S3_BUCKET_NAME": "test-bucket",
            "S3_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret"
        })
        
        try:
            # Act
            from src.models.config import SnapshotConfig
            config = SnapshotConfig()
            
            # Assert
            assert config.snapshot_hosts_list == ["http://localhost:9200", "http://localhost:9201"]
            assert config.indices_list == ["index1", "index2", "index3"]
            assert config.repository_name == "test-repo"
            assert config.bucket_name == "test-bucket"
            
        finally:
            # Cleanup
            for key in ["SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
                       "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
                       "AWS_SECRET_ACCESS_KEY"]:
                os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_snapshot_config_validators(self):
        """Test SnapshotConfig field validators."""
        # Test cases for different validation scenarios
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
            },
            {
                "name": "missing_access_key",
                "env_vars": {
                    "SNAPSHOT_HOSTS": "http://localhost:9200",
                    "ES_REPOSITORY_NAME": "test-repo",
                    "ES_INDICES": "test_index",
                    "S3_BUCKET_NAME": "test-bucket",
                    "S3_REGION": "us-east-1",
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
                from src.models.config import SnapshotConfig
                if test_case["should_succeed"]:
                    config = SnapshotConfig()
                    assert config is not None
                    print(f"✓ {test_case['name']} passed")
                else:
                    with pytest.raises(Exception):
                        SnapshotConfig()
                    print(f"✓ {test_case['name']} correctly failed")
                    
            finally:
                # Cleanup
                for key in test_case["env_vars"]:
                    os.environ.pop(key, None)


class TestSnapshotManagerIntegration:
    """Integration tests for SnapshotManager."""

    @pytest.mark.asyncio
    async def test_snapshot_manager_with_real_config(self):
        """Test SnapshotManager with real configuration loading."""
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
            manager = SnapshotManager()
            
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
    async def test_snapshot_manager_end_to_end_workflow(self):
        """Test end-to-end snapshot workflow with mocked dependencies."""
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
            # Create manager with real config
            manager = SnapshotManager()
            
            # Mock the snapshot and cleanup operations
            expected_snapshot_name = "snapshot_20250730_120000"
            expected_cleanup_result = {"total_deleted": 1, "total_kept": 3}
            
            with patch.object(manager, 'create_snapshot', return_value=expected_snapshot_name):
                with patch.object(manager, 'cleanup_old_snapshots', return_value=expected_cleanup_result):
                    # Act
                    result = await manager.run_snapshot_and_cleanup()
                    
                    # Assert
                    assert result["success"] is True
                    assert result["snapshot_name"] == expected_snapshot_name
                    assert result["cleanup_result"] == expected_cleanup_result
                    assert "timestamp" in result
                    
        finally:
            # Cleanup
            for key in ["SNAPSHOT_HOSTS", "ES_REPOSITORY_NAME", "ES_INDICES", 
                       "S3_BUCKET_NAME", "S3_REGION", "AWS_ACCESS_KEY_ID", 
                       "AWS_SECRET_ACCESS_KEY", "LOG_LEVEL", "LOG_FORMAT"]:
                os.environ.pop(key, None)

    @pytest.mark.asyncio
    async def test_snapshot_manager_configuration_validation(self):
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
                    manager = SnapshotManager()
                    assert manager.config is not None
                    print(f"✓ {test_case['name']} passed")
                else:
                    with pytest.raises(Exception):
                        SnapshotManager()
                    print(f"✓ {test_case['name']} correctly failed")
                    
            finally:
                # Cleanup
                for key in test_case["env_vars"]:
                    os.environ.pop(key, None)


if __name__ == "__main__":
    # Run tests without coverage for local testing
    pytest.main([__file__, "-v", "--no-cov"])