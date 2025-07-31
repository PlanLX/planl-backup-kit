"""Tests for ElasticsearchSnapshot class."""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from elasticsearch.exceptions import NotFoundError, RequestError

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.snapshot import ElasticsearchSnapshot
from src.models.config import SnapshotConfig


class TestElasticsearchSnapshot:
    """Test cases for ElasticsearchSnapshot class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock SnapshotConfig."""
        return SnapshotConfig(
            SNAPSHOT_HOSTS="http://localhost:9200",
            ES_REPOSITORY_NAME="s3_test_repo",
            ES_INDICES="test_index1,test_index2",
            S3_BUCKET_NAME="test-bucket",
            S3_REGION="us-east-1",
            AWS_ACCESS_KEY_ID="test-access-key",
            AWS_SECRET_ACCESS_KEY="test-secret-key",
            SNAPSHOT_TIMEOUT=30,
        )

    @pytest.fixture
    def snapshot_handler(self, mock_config):
        """Create ElasticsearchSnapshot instance."""
        return ElasticsearchSnapshot(mock_config)

    @pytest.fixture
    def mock_es_client(self):
        """Create a mock Elasticsearch client."""
        client = MagicMock()
        client.info.return_value = {"cluster_name": "test-cluster"}
        client.close = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_connect_success(self, snapshot_handler, mock_es_client):
        """Test successful connection to Elasticsearch."""
        with patch("src.core.snapshot.Elasticsearch", return_value=mock_es_client):
            await snapshot_handler.connect()
            
            assert snapshot_handler.es_client is not None
            mock_es_client.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_auth(self, mock_config):
        """Test connection with authentication."""
        mock_config.snapshot_username = "test_user"
        mock_config.snapshot_password = "test_pass"
        
        snapshot_handler = ElasticsearchSnapshot(mock_config)
        mock_es_client = MagicMock()
        mock_es_client.info.return_value = {"cluster_name": "test-cluster"}
        
        with patch("src.core.snapshot.Elasticsearch", return_value=mock_es_client) as mock_es:
            await snapshot_handler.connect()
            
            # Verify Elasticsearch was called with auth parameters
            mock_es.assert_called_once()
            call_args = mock_es.call_args[1]
            assert call_args["basic_auth"] == ("test_user", "test_pass")

    @pytest.mark.asyncio
    async def test_connect_failure(self, snapshot_handler):
        """Test connection failure."""
        with patch("src.core.snapshot.Elasticsearch", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await snapshot_handler.connect()

    @pytest.mark.asyncio
    async def test_create_repository_s3(self, snapshot_handler, mock_es_client):
        """Test creating S3 repository."""
        snapshot_handler.es_client = mock_es_client
        
        await snapshot_handler.create_repository()
        
        mock_es_client.snapshot.create_repository.assert_called_once()
        call_args = mock_es_client.snapshot.create_repository.call_args
        assert call_args[1]["name"] == "s3_test_repo"
        assert call_args[1]["body"]["type"] == "s3"
        assert call_args[1]["body"]["settings"]["bucket"] == "test-bucket"

    @pytest.mark.asyncio
    async def test_create_repository_fs(self, mock_config):
        """Test creating filesystem repository."""
        mock_config.repository_name = "fs_repo"
        snapshot_handler = ElasticsearchSnapshot(mock_config)
        mock_es_client = MagicMock()
        snapshot_handler.es_client = mock_es_client
        
        await snapshot_handler.create_repository()
        
        call_args = mock_es_client.snapshot.create_repository.call_args
        assert call_args[1]["body"]["type"] == "fs"

    @pytest.mark.asyncio
    async def test_create_repository_already_exists(self, snapshot_handler, mock_es_client):
        """Test creating repository that already exists."""
        snapshot_handler.es_client = mock_es_client
        
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
        await snapshot_handler.create_repository()

    @pytest.mark.asyncio
    async def test_create_repository_other_error(self, snapshot_handler, mock_es_client):
        """Test creating repository with other error."""
        snapshot_handler.es_client = mock_es_client
        
        from elasticsearch import TransportError
        error = TransportError(message="Internal server error")
        mock_es_client.snapshot.create_repository.side_effect = error
        
        with pytest.raises(TransportError):
            await snapshot_handler.create_repository()

    @pytest.mark.asyncio
    async def test_create_snapshot_auto_name(self, snapshot_handler, mock_es_client):
        """Test creating snapshot with auto-generated name."""
        snapshot_handler.es_client = mock_es_client
        mock_es_client.snapshot.create.return_value = {"snapshot": {"snapshot": "test_snapshot"}}
        
        with patch("src.core.snapshot.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.strftime.return_value = "20230101_120000"
            
            result = await snapshot_handler.create_snapshot()
            
            assert result == "snapshot_20230101_120000"
            mock_es_client.snapshot.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_custom_name(self, mock_config):
        """Test creating snapshot with custom name."""
        mock_config.snapshot_name = "custom_snapshot"
        snapshot_handler = ElasticsearchSnapshot(mock_config)
        mock_es_client = MagicMock()
        snapshot_handler.es_client = mock_es_client
        mock_es_client.snapshot.create.return_value = {"snapshot": {"snapshot": "custom_snapshot"}}
        
        result = await snapshot_handler.create_snapshot()
        
        assert result == "custom_snapshot"
        call_args = mock_es_client.snapshot.create.call_args
        assert call_args[1]["snapshot"] == "custom_snapshot"

    @pytest.mark.asyncio
    async def test_create_snapshot_failure(self, snapshot_handler, mock_es_client):
        """Test snapshot creation failure."""
        snapshot_handler.es_client = mock_es_client
        mock_es_client.snapshot.create.side_effect = Exception("Snapshot creation failed")
        
        with pytest.raises(Exception, match="Snapshot creation failed"):
            await snapshot_handler.create_snapshot()

    @pytest.mark.asyncio
    async def test_get_snapshot_status_success(self, snapshot_handler, mock_es_client):
        """Test getting snapshot status successfully."""
        snapshot_handler.es_client = mock_es_client
        expected_status = {"snapshot": "test_snapshot", "state": "SUCCESS"}
        mock_es_client.snapshot.get.return_value = expected_status
        
        result = await snapshot_handler.get_snapshot_status("test_snapshot")
        
        assert result == expected_status
        mock_es_client.snapshot.get.assert_called_once_with(
            repository="s3_test_repo", snapshot="test_snapshot"
        )

    @pytest.mark.asyncio
    async def test_get_snapshot_status_not_found(self, snapshot_handler, mock_es_client):
        """Test getting snapshot status when not found."""
        snapshot_handler.es_client = mock_es_client
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        error = NotFoundError(404, "not_found", "Snapshot not found")
        mock_es_client.snapshot.get.side_effect = error
        
        result = await snapshot_handler.get_snapshot_status("nonexistent_snapshot")
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_list_snapshots_success(self, snapshot_handler, mock_es_client):
        """Test listing snapshots successfully."""
        snapshot_handler.es_client = mock_es_client
        expected_snapshots = [
            {"snapshot": "snapshot1", "state": "SUCCESS"},
            {"snapshot": "snapshot2", "state": "SUCCESS"}
        ]
        mock_es_client.snapshot.get.return_value = {"snapshots": expected_snapshots}
        
        result = await snapshot_handler.list_snapshots()
        
        assert result == expected_snapshots
        mock_es_client.snapshot.get.assert_called_once_with(
            repository="s3_test_repo", snapshot="_all"
        )

    @pytest.mark.asyncio
    async def test_list_snapshots_failure(self, snapshot_handler, mock_es_client):
        """Test listing snapshots failure."""
        snapshot_handler.es_client = mock_es_client
        mock_es_client.snapshot.get.side_effect = Exception("List snapshots failed")
        
        with pytest.raises(Exception, match="List snapshots failed"):
            await snapshot_handler.list_snapshots()

    @pytest.mark.asyncio
    async def test_delete_snapshot_success(self, snapshot_handler, mock_es_client):
        """Test deleting snapshot successfully."""
        snapshot_handler.es_client = mock_es_client
        
        await snapshot_handler.delete_snapshot("test_snapshot")
        
        mock_es_client.snapshot.delete.assert_called_once_with(
            repository="s3_test_repo", snapshot="test_snapshot"
        )

    @pytest.mark.asyncio
    async def test_delete_snapshot_failure(self, snapshot_handler, mock_es_client):
        """Test deleting snapshot failure."""
        snapshot_handler.es_client = mock_es_client
        mock_es_client.snapshot.delete.side_effect = Exception("Delete failed")
        
        with pytest.raises(Exception, match="Delete failed"):
            await snapshot_handler.delete_snapshot("test_snapshot")

    @pytest.mark.asyncio
    async def test_close_connection(self, snapshot_handler, mock_es_client):
        """Test closing Elasticsearch connection."""
        snapshot_handler.es_client = mock_es_client
        
        await snapshot_handler.close()
        
        mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_snapshot_complete_operation(self, snapshot_handler, mock_es_client):
        """Test complete snapshot operation."""
        mock_es_client.snapshot.create.return_value = {"snapshot": {"snapshot": "test_snapshot"}}
        
        with patch("src.core.snapshot.Elasticsearch", return_value=mock_es_client):
            result = await snapshot_handler.snapshot()
            
            # Check that result is a valid snapshot name format
            assert result.startswith("snapshot_")
            assert len(result) > 10  # Should have timestamp
            mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots_no_retention(self, snapshot_handler):
        """Test cleanup with no retention settings."""
        # Mock the config to have no retention settings
        snapshot_handler.config.retention_days = None
        snapshot_handler.config.retention_count = None
        
        # Should not raise any exceptions and should return early
        await snapshot_handler.cleanup_old_snapshots()

    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots_with_retention(self, mock_config):
        """Test cleanup with retention settings."""
        mock_config.retention_count = 5
        mock_config.retention_days = 7
        snapshot_handler = ElasticsearchSnapshot(mock_config)
        
        mock_snapshots = [
            {"snapshot": "snapshot1", "start_time": "2023-01-01T10:00:00.000Z"},
            {"snapshot": "snapshot2", "start_time": "2023-01-02T10:00:00.000Z"},
            {"snapshot": "snapshot3", "start_time": "2023-01-03T10:00:00.000Z"},
        ]
        
        mock_es_client = MagicMock()
        mock_es_client.snapshot.get.return_value = {"snapshots": mock_snapshots}
        
        with patch("src.core.snapshot.Elasticsearch", return_value=mock_es_client):
            await snapshot_handler.cleanup_old_snapshots()
            
            # Should call delete for old snapshots
            assert mock_es_client.snapshot.delete.called 