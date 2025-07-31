"""Tests for SnapshotRotation class."""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from elasticsearch.exceptions import NotFoundError, RequestError

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.rotation import SnapshotRotation
from src.models.config import SnapshotConfig


class TestSnapshotRotation:
    """Test cases for SnapshotRotation class."""

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
    def rotation_handler(self, mock_config):
        """Create SnapshotRotation instance."""
        return SnapshotRotation(mock_config)

    @pytest.fixture
    def mock_es_client(self):
        """Create a mock Elasticsearch client."""
        client = MagicMock()
        client.info.return_value = {"cluster_name": "test-cluster"}
        client.close = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_connect_success(self, rotation_handler, mock_es_client):
        """Test successful connection to Elasticsearch."""
        with patch("src.core.rotation.Elasticsearch", return_value=mock_es_client):
            await rotation_handler.connect()
            
            assert rotation_handler.es_client is not None
            mock_es_client.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_auth(self, mock_config):
        """Test connection with authentication."""
        mock_config.snapshot_username = "test_user"
        mock_config.snapshot_password = "test_pass"
        
        rotation_handler = SnapshotRotation(mock_config)
        mock_es_client = MagicMock()
        mock_es_client.info.return_value = {"cluster_name": "test-cluster"}
        
        with patch("src.core.rotation.Elasticsearch", return_value=mock_es_client) as mock_es:
            await rotation_handler.connect()
            
            # Verify Elasticsearch was called with auth parameters
            mock_es.assert_called_once()
            call_args = mock_es.call_args[1]
            assert call_args["basic_auth"] == ("test_user", "test_pass")

    @pytest.mark.asyncio
    async def test_connect_failure(self, rotation_handler):
        """Test connection failure."""
        with patch("src.core.rotation.Elasticsearch", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await rotation_handler.connect()

    @pytest.mark.asyncio
    async def test_create_repository_s3(self, rotation_handler, mock_es_client):
        """Test creating S3 repository."""
        rotation_handler.es_client = mock_es_client
        
        await rotation_handler.create_repository()
        
        mock_es_client.snapshot.create_repository.assert_called_once()
        call_args = mock_es_client.snapshot.create_repository.call_args
        assert call_args[1]["name"] == "s3_test_repo"
        assert call_args[1]["body"]["type"] == "s3"
        assert call_args[1]["body"]["settings"]["bucket"] == "test-bucket"

    @pytest.mark.asyncio
    async def test_create_repository_fs(self, mock_config):
        """Test creating filesystem repository."""
        mock_config.repository_name = "fs_repo"
        rotation_handler = SnapshotRotation(mock_config)
        mock_es_client = MagicMock()
        rotation_handler.es_client = mock_es_client
        
        await rotation_handler.create_repository()
        
        call_args = mock_es_client.snapshot.create_repository.call_args
        assert call_args[1]["body"]["type"] == "fs"

    @pytest.mark.asyncio
    async def test_create_repository_already_exists(self, rotation_handler, mock_es_client):
        """Test creating repository that already exists."""
        rotation_handler.es_client = mock_es_client
        
        # Create a proper RequestError with meta object
        from elasticsearch import RequestError
        from elastic_transport import ApiResponseMeta
        
        meta = ApiResponseMeta(status=400, http_version="1.1", headers={}, duration=0.0, node=None)
        error = RequestError(
            message="repository [s3_test_repo] already exists", 
            meta=meta,
            body={}
        )
        mock_es_client.snapshot.create_repository.side_effect = error
        
        # Should not raise an exception
        await rotation_handler.create_repository()

    @pytest.mark.asyncio
    async def test_list_snapshots_success(self, rotation_handler, mock_es_client):
        """Test listing snapshots successfully."""
        rotation_handler.es_client = mock_es_client
        expected_snapshots = [
            {"snapshot": "snapshot1", "state": "SUCCESS"},
            {"snapshot": "snapshot2", "state": "SUCCESS"}
        ]
        mock_es_client.snapshot.get.return_value = {"snapshots": expected_snapshots}
        
        result = await rotation_handler.list_snapshots()
        
        assert result == expected_snapshots
        mock_es_client.snapshot.get.assert_called_once_with(
            repository="s3_test_repo", snapshot="_all"
        )

    @pytest.mark.asyncio
    async def test_list_snapshots_failure(self, rotation_handler, mock_es_client):
        """Test listing snapshots failure."""
        rotation_handler.es_client = mock_es_client
        mock_es_client.snapshot.get.side_effect = Exception("List snapshots failed")
        
        with pytest.raises(Exception, match="List snapshots failed"):
            await rotation_handler.list_snapshots()

    @pytest.mark.asyncio
    async def test_delete_snapshot_success(self, rotation_handler, mock_es_client):
        """Test deleting snapshot successfully."""
        rotation_handler.es_client = mock_es_client
        
        await rotation_handler.delete_snapshot("test_snapshot")
        
        mock_es_client.snapshot.delete.assert_called_once_with(
            repository="s3_test_repo", snapshot="test_snapshot", request_timeout=30
        )

    @pytest.mark.asyncio
    async def test_delete_snapshot_not_found(self, rotation_handler, mock_es_client):
        """Test deleting snapshot that doesn't exist."""
        rotation_handler.es_client = mock_es_client
        
        # Create a proper NotFoundError
        from elasticsearch import NotFoundError
        error = NotFoundError(404, "not_found", "Snapshot not found")
        mock_es_client.snapshot.delete.side_effect = error
        
        # Should not raise an exception
        await rotation_handler.delete_snapshot("nonexistent_snapshot")

    @pytest.mark.asyncio
    async def test_delete_snapshot_failure(self, rotation_handler, mock_es_client):
        """Test deleting snapshot failure."""
        rotation_handler.es_client = mock_es_client
        mock_es_client.snapshot.delete.side_effect = Exception("Delete failed")
        
        with pytest.raises(Exception, match="Delete failed"):
            await rotation_handler.delete_snapshot("test_snapshot")

    def test_parse_snapshot_date_snapshot_format(self, rotation_handler):
        """Test parsing snapshot date with snapshot_ format."""
        snapshot_name = "snapshot_20250729_130424"
        result = rotation_handler.parse_snapshot_date(snapshot_name)
        
        expected_date = datetime(2025, 7, 29, 13, 4, 24)
        assert result == expected_date

    def test_parse_snapshot_date_compact_format(self, rotation_handler):
        """Test parsing snapshot date with compact format."""
        snapshot_name = "snapshot20250729_131212"
        result = rotation_handler.parse_snapshot_date(snapshot_name)
        
        expected_date = datetime(2025, 7, 29, 13, 12, 12)
        assert result == expected_date

    def test_parse_snapshot_date_invalid_format(self, rotation_handler):
        """Test parsing snapshot date with invalid format."""
        snapshot_name = "invalid_snapshot_name"
        result = rotation_handler.parse_snapshot_date(snapshot_name)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_rotate_snapshots_no_snapshots(self, rotation_handler, mock_es_client):
        """Test rotation with no snapshots."""
        rotation_handler.es_client = mock_es_client
        mock_es_client.snapshot.get.return_value = {"snapshots": []}
        
        result = await rotation_handler.rotate_snapshots()
        
        assert result["deleted"] == []
        assert result["kept"] == []
        assert result["total_deleted"] == 0

    @pytest.mark.asyncio
    async def test_rotate_snapshots_max_count(self, rotation_handler, mock_es_client):
        """Test rotation based on maximum count."""
        rotation_handler.es_client = mock_es_client
        
        # 使用接近当前日期的快照日期，避免年龄限制的影响
        snapshots = [
            {
                "snapshot": "snapshot_20250731_100000",  # 最新的
                "state": "SUCCESS"
            },
            {
                "snapshot": "snapshot_20250730_100000",  # 中等的
                "state": "SUCCESS"
            },
            {
                "snapshot": "snapshot_20250729_100000",  # 最旧的
                "state": "SUCCESS"
            }
        ]
        mock_es_client.snapshot.get.return_value = {"snapshots": snapshots}
        
        # Mock the delete_snapshot method to avoid actually deleting
        rotation_handler.delete_snapshot = AsyncMock()
        
        result = await rotation_handler.rotate_snapshots(max_snapshots=2)
        
        # 应该保留最新的2个快照，删除最旧的1个快照
        assert result["total_deleted"] == 1
        assert result["total_kept"] == 2

    @pytest.mark.asyncio
    async def test_rotate_snapshots_max_age(self, rotation_handler, mock_es_client):
        """Test rotation based on maximum age."""
        rotation_handler.es_client = mock_es_client
        
        # Create old snapshots (40天前)
        old_date = datetime.now() - timedelta(days=40)
        old_snapshot_name = f"snapshot_{old_date.strftime('%Y%m%d_%H%M%S')}"
        
        # Create newer snapshot (今天)
        new_date = datetime.now()
        new_snapshot_name = f"snapshot_{new_date.strftime('%Y%m%d_%H%M%S')}"
        
        snapshots = [
            {
                "snapshot": new_snapshot_name,  # 新的快照
                "state": "SUCCESS"
            },
            {
                "snapshot": old_snapshot_name,  # 旧的快照
                "state": "SUCCESS"
            }
        ]
        mock_es_client.snapshot.get.return_value = {"snapshots": snapshots}
        
        result = await rotation_handler.rotate_snapshots(max_age_days=30)
        
        # 应该删除旧的快照(40天前)，保留新的快照
        assert result["total_deleted"] == 1
        assert result["total_kept"] == 1

    @pytest.mark.asyncio
    async def test_rotate_snapshots_keep_successful_only(self, rotation_handler, mock_es_client):
        """Test rotation keeping only successful snapshots."""
        rotation_handler.es_client = mock_es_client
        
        # Create snapshots with current dates
        current_date = datetime.now()
        snapshot_name = f"snapshot_{current_date.strftime('%Y%m%d_%H%M%S')}"
        old_date = current_date - timedelta(days=1)
        old_snapshot_name = f"snapshot_{old_date.strftime('%Y%m%d_%H%M%S')}"
        
        snapshots = [
            {
                "snapshot": snapshot_name,
                "state": "SUCCESS"
            },
            {
                "snapshot": old_snapshot_name,
                "state": "FAILED"
            }
        ]
        mock_es_client.snapshot.get.return_value = {"snapshots": snapshots}
        
        result = await rotation_handler.rotate_snapshots(keep_successful_only=True)
        
        # Should only process successful snapshots
        assert result["total_kept"] == 1
        assert len(result["kept"]) == 1

    @pytest.mark.asyncio
    async def test_close_connection(self, rotation_handler, mock_es_client):
        """Test closing Elasticsearch connection."""
        rotation_handler.es_client = mock_es_client
        
        await rotation_handler.close()
        
        mock_es_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_rotate_complete_operation(self, rotation_handler, mock_es_client):
        """Test complete rotation operation."""
        mock_es_client.snapshot.get.return_value = {"snapshots": []}
        
        with patch("src.core.rotation.Elasticsearch", return_value=mock_es_client):
            result = await rotation_handler.rotate()
            
            assert result["total_deleted"] == 0
            assert result["total_kept"] == 0
            mock_es_client.close.assert_called_once() 