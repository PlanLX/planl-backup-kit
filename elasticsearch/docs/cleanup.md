# Elasticsearch Cleanup Tool

This tool provides a standalone cleanup functionality for Elasticsearch snapshots, designed to work with S3 repositories.

## Features

- Clean up snapshots by name
- Clean up all snapshots
- Clean up snapshots matching a pattern
- Clean up snapshots older than a specific date
- Dry run mode to preview deletions
- Configuration via environment variables

## Usage

### Environment Variables

The cleanup tool requires the following environment variables:

```bash
# Elasticsearch connection
export SNAPSHOT_HOSTS=http://localhost:9200
export ES_REPOSITORY_NAME=my-s3-repository
export ES_INDICES=index1,index2

# S3 configuration
export S3_BUCKET_NAME=my-backup-bucket
export S3_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional logging configuration
export LOG_LEVEL=INFO
export LOG_FORMAT=plain
```

### Running the Cleanup Tool

```bash
# Clean up all snapshots
python cleanup.py --all

# Clean up specific snapshots
python cleanup.py --names snapshot_1,snapshot_2

# Clean up snapshots matching a pattern
python cleanup.py --pattern "snapshot_2025*"

# Clean up snapshots older than a date
python cleanup.py --older-than "2025-07-01"

# Dry run mode (preview deletions without actually deleting)
python cleanup.py --all --dry-run
```

### Using the CLI Command

After installing the package, you can also use the CLI command:

```bash
# Clean up all snapshots
es-cleanup --all

# Clean up specific snapshots
es-cleanup --names snapshot_1,snapshot_2

# Clean up snapshots matching a pattern
es-cleanup --pattern "snapshot_2025*"

# Clean up snapshots older than a date
es-cleanup --older-than "2025-07-01"

# Dry run mode
es-cleanup --all --dry-run
```

## Testing

Run the tests with:

```bash
python -m pytest tests/test_cleanup_manager.py -v
```