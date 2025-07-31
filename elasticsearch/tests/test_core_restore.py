"""Tests for ElasticsearchRestore class."""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from elasticsearch.exceptions import NotFoundError, RequestError

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.restore import ElasticsearchRestore
from src.models.config import RestoreConfig


class TestElasticsearchRestore:
    """Test cases for ElasticsearchRestore class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock RestoreConfig for restore."""
        return RestoreConfig(
            RESTORE_HOSTS="http://localhost:9200",
            ES_REPOSITORY_NAME="s3_test_repo",
            ES_SNAPSHOT_NAME="test_snapshot",
            ES_INDICES="test_index1,test_index2",
            S3_BUCKET_NAME="test-bucket",
            S3_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test-access-key",
            AWS_SECRET_ACCESS_KEY="test-secret-key",
        )

    @pytest.fixture
    def restore_handler(self, mock_config):
        """Create ElasticsearchRestore instance."""
        return ElasticsearchRestore(mock_config)

    @pytest.fixture
    def mock_es_client(self):
        """Create a mock Elasticsearch client."""
        client = MagicMock()
        client.info.return_value = {"cluster_name": "test-cluster"}
        client.close = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_connect_success(self, restore_handler, mock_es_client):
        """Test successful connection to Elasticsearch."""
        with patch("src.core.restore.Elasticsearch", return_value=mock_es_client):
            await restore_handler.connect()
            
            assert restore_handler.es_client is not None
            mock_es_client.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_auth(self, mock_config):
        """Test connection with authentication."""
        mock_config.restore_username = "test_user"
        mock_config.restore_password = "test_pass"
        
        restore_handler = ElasticsearchRestore(mock_config)
        mock_es_client = MagicMock()
        mock_es_client.info.return_value = {"cluster_name": "test-cluster"}
        
        with patch("src.core.restore.Elasticsearch", return_value=mock_es_client) as mock_es:
            await restore_handler.connect()
            
            # Verify Elasticsearch was called with auth parameters
            mock_es.assert_called_once()
            call_args = mock_es.call_args[1]
            assert call_args["basic_auth"] == ("test_user", "test_pass")

    @pytest.mark.asyncio
    async def test_connect_failure(self, restore_handler):
        """Test connection failure."""
        with patch("src.core.restore.Elasticsearch", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await restore_handler.connect()

    @pytest.mark.asyncio
    async def test_create_repository_s3(self, restore_handler, mock_es_client):
        """Test creating S3 repository."""
        restore_handler.es_client = mock_es_client
        
        await restore_handler.create_repository()
        
        mock_es_client.snapshot.create_repository.assert_called_once()
        call_args = mock_es_client.snapshot.create_repository.call_args
        assert call_args[1]["name"] == "s3_test_repo"
        assert call_args[1]["body"]["type"] == "s3"
        assert call_args[1]["body"]["settings"]["bucket"] == "test-bucket"

    @pytest.mark.asyncio
    async def test_create_repository_fs(self, mock_config):
        """Test creating filesystem repository."""
        mock_config.repository_name = "fs_repo"
        restore_handler = ElasticsearchRestore(mock_config)
        mock_es_client = MagicMock()
        restore_handler.es_client = mock_es_client
        
        await restore_handler.create_repository()
        
        call_args = mock_es_client.snapshot.create_repository.call_args
        assert call_args[1]["body"]["type"] == "fs"

    @pytest.mark.asyncio
    async def test_create_repository_already_exists(self, restore_handler, mock_es_client):
        """Test creating repository that already exists."""
        restore_handler.es_client = mock_es_client
        
        # Create a mock RequestError that matches the expected behavior
        from elasticsearch import RequestError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=400, http_version="1.1", headers={}, duration=0.0, node=None)
        error = RequestError(
            message="repository [s3_test_repo] already exists", 
            meta=meta,
            body={}
        )
        
        mock_es_client.snapshot.create_repository.side_effect = error
        
        # Should not raise an exception (should be caught and logged)
        await restore_handler.create_repository()

    @pytest.mark.asyncio
    async def test_snapshot_exists_true(self, restore_handler, mock_es_client):
        """Test checking snapshot existence when it exists."""
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.get.return_value = {"snapshot": "test_snapshot"}
        
        result = await restore_handler.snapshot_exists("test_snapshot")
        
        assert result is True
        mock_es_client.snapshot.get.assert_called_once_with(
            repository="s3_test_repo", snapshot="test_snapshot"
        )

    @pytest.mark.asyncio
    async def test_snapshot_exists_false(self, restore_handler, mock_es_client):
        """Test checking snapshot existence when it doesn't exist."""
        restore_handler.es_client = mock_es_client
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=404, http_version="1.1", headers={}, duration=0.0, node=None)
        error = NotFoundError(meta, "Snapshot not found", {})
        
        mock_es_client.snapshot.get.side_effect = error
        
        result = await restore_handler.snapshot_exists("nonexistent_snapshot")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_snapshot_exists_error(self, restore_handler, mock_es_client):
        """Test checking snapshot existence with error."""
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.get.side_effect = Exception("Unexpected error")
        
        with pytest.raises(Exception, match="Unexpected error"):
            await restore_handler.snapshot_exists("test_snapshot")

    @pytest.mark.asyncio
    async def test_close_indices_success(self, restore_handler, mock_es_client):
        """Test closing indices successfully."""
        restore_handler.es_client = mock_es_client
        
        await restore_handler.close_indices(["index1", "index2"])
        
        assert mock_es_client.indices.close.call_count == 2
        mock_es_client.indices.close.assert_any_call(
            index="index1", ignore_unavailable=True, request_timeout=300
        )
        mock_es_client.indices.close.assert_any_call(
            index="index2", ignore_unavailable=True, request_timeout=300
        )

    @pytest.mark.asyncio
    async def test_close_indices_not_found(self, restore_handler, mock_es_client):
        """Test closing indices that don't exist."""
        restore_handler.es_client = mock_es_client
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=404, http_version="1.1", headers={}, duration=0.0, node=None)
        error = NotFoundError(meta, "Index not found", {})
        
        mock_es_client.indices.close.side_effect = error
        
        # Should not raise an exception
        await restore_handler.close_indices(["nonexistent_index"])

    @pytest.mark.asyncio
    async def test_close_indices_error(self, restore_handler, mock_es_client):
        """Test closing indices with error."""
        restore_handler.es_client = mock_es_client
        mock_es_client.indices.close.side_effect = Exception("Close failed")
        
        with pytest.raises(Exception, match="Close failed"):
            await restore_handler.close_indices(["index1"])

    @pytest.mark.asyncio
    async def test_open_indices_success(self, restore_handler, mock_es_client):
        """Test opening indices successfully."""
        restore_handler.es_client = mock_es_client
        
        await restore_handler.open_indices(["index1", "index2"])
        
        assert mock_es_client.indices.open.call_count == 2
        mock_es_client.indices.open.assert_any_call(
            index="index1", ignore_unavailable=True, request_timeout=300
        )
        mock_es_client.indices.open.assert_any_call(
            index="index2", ignore_unavailable=True, request_timeout=300
        )

    @pytest.mark.asyncio
    async def test_open_indices_not_found(self, restore_handler, mock_es_client):
        """Test opening indices that don't exist."""
        restore_handler.es_client = mock_es_client
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=404, http_version="1.1", headers={}, duration=0.0, node=None)
        error = NotFoundError(meta, "Index not found", {})
        
        mock_es_client.indices.open.side_effect = error
        
        # Should not raise an exception
        await restore_handler.open_indices(["nonexistent_index"])

    @pytest.mark.asyncio
    async def test_restore_snapshot_success(self, restore_handler, mock_es_client):
        """Test restoring snapshot successfully."""
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.restore.return_value = {"accepted": True}
        
        await restore_handler.restore_snapshot("test_snapshot")
        
        mock_es_client.snapshot.restore.assert_called_once()
        call_args = mock_es_client.snapshot.restore.call_args
        assert call_args[1]["repository"] == "s3_test_repo"
        assert call_args[1]["snapshot"] == "test_snapshot"
        assert "indices" in call_args[1]["body"]

    @pytest.mark.asyncio
    async def test_restore_snapshot_with_rename(self, mock_config):
        """Test restoring snapshot with rename pattern."""
        mock_config.rename_pattern = "old_(.+)"
        mock_config.rename_replacement = "new_$1"
        restore_handler = ElasticsearchRestore(mock_config)
        mock_es_client = MagicMock()
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.restore.return_value = {"accepted": True}
        
        await restore_handler.restore_snapshot("test_snapshot")
        
        call_args = mock_es_client.snapshot.restore.call_args
        restore_body = call_args[1]["body"]
        assert restore_body["rename_pattern"] == "old_(.+)"
        assert restore_body["rename_replacement"] == "new_$1"

    @pytest.mark.asyncio
    async def test_restore_snapshot_empty_name(self, restore_handler):
        """Test restoring snapshot with empty name."""
        with pytest.raises(ValueError, match="Snapshot name is required"):
            await restore_handler.restore_snapshot("")

    @pytest.mark.asyncio
    async def test_restore_snapshot_failure(self, restore_handler, mock_es_client):
        """Test restoring snapshot failure."""
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.restore.side_effect = Exception("Restore failed")
        
        with pytest.raises(Exception, match="Restore failed"):
            await restore_handler.restore_snapshot("test_snapshot")

    @pytest.mark.asyncio
    async def test_restore_snapshot_failure_reopen_indices(self, restore_handler, mock_es_client):
        """Test that indices are reopened after restore failure."""
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.restore.side_effect = Exception("Restore failed")
        
        with pytest.raises(Exception, match="Restore failed"):
            await restore_handler.restore_snapshot("test_snapshot")
        
        # Should attempt to reopen indices
        assert mock_es_client.indices.open.called

    @pytest.mark.asyncio
    async def test_get_snapshot_status_success(self, restore_handler, mock_es_client):
        """Test getting snapshot status successfully."""
        restore_handler.es_client = mock_es_client
        expected_status = {"snapshot": "test_snapshot", "state": "SUCCESS"}
        mock_es_client.snapshot.get.return_value = expected_status
        
        result = await restore_handler.get_snapshot_status("test_snapshot")
        
        assert result == expected_status
        mock_es_client.snapshot.get.assert_called_once_with(
            repository="s3_test_repo", snapshot="test_snapshot"
        )

    @pytest.mark.asyncio
    async def test_get_snapshot_status_not_found(self, restore_handler, mock_es_client):
        """Test getting snapshot status when not found."""
        restore_handler.es_client = mock_es_client
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=404, http_version="1.1", headers={}, duration=0.0, node=None)
        error = NotFoundError(meta, "Snapshot not found", {})
        
        mock_es_client.snapshot.get.side_effect = error
        
        result = await restore_handler.get_snapshot_status("nonexistent_snapshot")
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_snapshots_success(self, restore_handler, mock_es_client):
        """Test listing snapshots successfully."""
        restore_handler.es_client = mock_es_client
        expected_snapshots = [
            {"snapshot": "snapshot1", "state": "SUCCESS"},
            {"snapshot": "snapshot2", "state": "SUCCESS"}
        ]
        mock_es_client.snapshot.get.return_value = {"snapshots": expected_snapshots}
        
        result = await restore_handler.list_snapshots()
        
        assert result == expected_snapshots
        mock_es_client.snapshot.get.assert_called_once_with(
            repository="s3_test_repo", snapshot="_all"
        )

    @pytest.mark.asyncio
    async def test_close_connection(self, restore_handler, mock_es_client):
        """Test closing Elasticsearch connection."""
        restore_handler.es_client = mock_es_client
        
        await restore_handler.close()
        
        mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_complete_operation_success(self, restore_handler, mock_es_client):
        """Test complete restore operation."""
        mock_es_client.snapshot.get.return_value = {"snapshot": "test_snapshot"}
        mock_es_client.snapshot.restore.return_value = {"accepted": True}
        
        with patch("src.core.restore.Elasticsearch", return_value=mock_es_client):
            await restore_handler.restore("test_snapshot")
            
            mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_complete_operation_snapshot_not_found(self, restore_handler, mock_es_client):
        """Test complete restore operation when snapshot doesn't exist."""
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=404, http_version="1.1", headers={}, duration=0.0, node=None)
        error = NotFoundError(meta, "Snapshot not found", {})
        
        mock_es_client.snapshot.get.side_effect = error
        
        with patch("src.core.restore.Elasticsearch", return_value=mock_es_client):
            with pytest.raises(ValueError, match="Snapshot 'test_snapshot' not found"):
                await restore_handler.restore("test_snapshot")
            
            mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_with_custom_settings(self, mock_config):
        """Test restore with custom settings."""
        mock_config.ignore_unavailable = False
        mock_config.partial = True
        restore_handler = ElasticsearchRestore(mock_config)
        mock_es_client = MagicMock()
        restore_handler.es_client = mock_es_client
        mock_es_client.snapshot.get.return_value = {"snapshot": "test_snapshot"}
        mock_es_client.snapshot.restore.return_value = {"accepted": True}
        
        await restore_handler.restore_snapshot("test_snapshot")
        
        call_args = mock_es_client.snapshot.restore.call_args
        restore_body = call_args[1]["body"]
        assert restore_body["ignore_unavailable"] is False
        assert restore_body["partial"] is True 