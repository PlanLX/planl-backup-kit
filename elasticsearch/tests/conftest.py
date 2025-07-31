"""Pytest configuration and shared fixtures."""

import pytest
import sys
import os
from unittest.mock import MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.config import SnapshotConfig


@pytest.fixture
def mock_snapshot_config():
    """Create a mock SnapshotConfig for testing."""
    return SnapshotConfig(
        SNAPSHOT_HOSTS="http://localhost:9200",
        RESTORE_HOSTS="http://localhost:9201",
        ES_REPOSITORY_NAME="s3_test_repo",
        ES_INDICES="test_index1,test_index2",
        S3_BUCKET_NAME="test-bucket",
        S3_REGION="us-east-1",
        AWS_ACCESS_KEY_ID="test-access-key",
        AWS_SECRET_ACCESS_KEY="test-secret-key",
        SNAPSHOT_TIMEOUT=30,
    )


@pytest.fixture
def mock_elasticsearch_client():
    """Create a mock Elasticsearch client."""
    client = MagicMock()
    client.info.return_value = {"cluster_name": "test-cluster"}
    client.close = MagicMock()
    return client


@pytest.fixture
def mock_snapshot_response():
    """Create a mock snapshot response."""
    return {
        "snapshots": [
            {
                "snapshot": "snapshot_20250101_100000",
                "uuid": "test-uuid-1",
                "version_id": 7170099,
                "version": "7.17.0",
                "indices": ["test_index1", "test_index2"],
                "state": "SUCCESS",
                "start_time": "2025-01-01T10:00:00.000Z",
                "start_time_in_millis": 1735725600000,
                "end_time": "2025-01-01T10:05:00.000Z",
                "end_time_in_millis": 1735725900000,
                "duration_in_millis": 300000,
                "failures": [],
                "shards": {
                    "total": 2,
                    "failed": 0,
                    "successful": 2
                }
            }
        ]
    }


@pytest.fixture
def mock_snapshot_status():
    """Create a mock snapshot status response."""
    return {
        "snapshot": "snapshot_20250101_100000",
        "uuid": "test-uuid-1",
        "version_id": 7170099,
        "version": "7.17.0",
        "indices": ["test_index1", "test_index2"],
        "state": "SUCCESS",
        "start_time": "2025-01-01T10:00:00.000Z",
        "start_time_in_millis": 1735725600000,
        "end_time": "2025-01-01T10:05:00.000Z",
        "end_time_in_millis": 1735725900000,
        "duration_in_millis": 300000,
        "failures": [],
        "shards": {
            "total": 2,
            "failed": 0,
            "successful": 2
        }
    }


@pytest.fixture
def mock_repository_status():
    """Create a mock repository status response."""
    return {
        "s3_test_repo": {
            "type": "s3",
            "settings": {
                "bucket": "test-bucket",
                "base_path": "elasticsearch-snapshots",
                "region": "us-east-1"
            }
        }
    }


@pytest.fixture
def mock_cluster_info():
    """Create a mock cluster info response."""
    return {
        "cluster_name": "test-cluster",
        "cluster_uuid": "test-cluster-uuid",
        "version": {
            "number": "7.17.0",
            "build_flavor": "default",
            "build_type": "tar",
            "build_hash": "test-hash",
            "build_date": "2023-01-01T00:00:00.000Z",
            "build_snapshot": False,
            "lucene_version": "8.11.1",
            "minimum_wire_compatibility_version": "6.8.0",
            "minimum_index_compatibility_version": "6.0.0-beta1"
        },
        "tagline": "You Know, for Search"
    } 