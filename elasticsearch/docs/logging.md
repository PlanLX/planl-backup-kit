# 日志配置指南

## 概述

本工具支持四种日志格式，可通过环境变量 `LOG_FORMAT` 进行配置：

- `json`: 结构化 JSON 格式，适合日志采集器
- `plain`: 纯文本格式，包含时间戳和结构化信息
- `console`: 彩色控制台格式，使用 Rich 库提供美观的终端输出
- `syslog`: Syslog 兼容格式，适合系统日志集成

## 配置选项

### 环境变量

```bash
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# 日志格式 (json, plain, console, syslog)
LOG_FORMAT=json
```

### 默认值

- `LOG_LEVEL`: `INFO`
- `LOG_FORMAT`: `json`

## 日志格式示例

### JSON 格式 (LOG_FORMAT=json)

```json
{"timestamp": "2025-07-30T11:24:56.123Z", "level": "INFO", "logger": "snapshot", "message": "Starting snapshot creation"}
{"timestamp": "2025-07-30T11:24:56.124Z", "level": "INFO", "logger": "snapshot", "message": "Snapshot configuration", "snapshot_cluster": ["http://192.168.1.105:9200"], "indices": ["index1", "index2"], "s3_bucket": "my-bucket", "repository": "my-repo"}
{"timestamp": "2025-07-30T11:24:56.125Z", "level": "INFO", "logger": "snapshot", "message": "Snapshot created successfully", "snapshot_name": "snapshot_20250730_112456"}
```

### 纯文本格式 (LOG_FORMAT=plain)

**标准格式：**
```
2025-07-29 12:00:00 INFO Starting snapshot creation
2025-07-29 12:00:01 INFO Snapshot configuration | snapshot_cluster=['http://192.168.1.105:9200'] | indices=['index1', 'index2'] | s3_bucket=my-bucket | repository=my-repo
2025-07-29 12:00:02 INFO Snapshot created successfully | snapshot_name=snapshot_20250730_112456
```

**用户操作日志格式参考：**
```
2025-07-29 12:00:00 INFO User successfully logged in (User ID: 12345, IP: 192.168.1.1)
2025-07-29 12:00:01 INFO Snapshot backup completed (Snapshot: backup_20250729_120001, Size: 2.5GB, Duration: 120s)
2025-07-29 12:00:02 ERROR Failed to connect to Elasticsearch (Host: 192.168.1.100, Port: 9200, Error: Connection timeout)
```

### Console 格式 (LOG_FORMAT=console)

**彩色控制台输出：**
```
2025-07-29 12:00:00 INFO Starting snapshot creation
2025-07-29 12:00:01 INFO Snapshot configuration | snapshot_cluster=['http://192.168.1.105:9200'] | indices=['index1', 'index2'] | s3_bucket=my-bucket | repository=my-repo
2025-07-29 12:00:02 INFO Snapshot created successfully | snapshot_name=snapshot_20250730_112456
✓ Snapshot created successfully!
⚠ Some snapshots are old
✗ Failed to connect to Elasticsearch
```

**表格输出示例：**
```
                         快照列表                          
╭──────────────────────────┬─────────┬───────┬────────────╮
│ 快照名称                 │ 状态    │ 大小  │ 日期       │
├──────────────────────────┼─────────┼───────┼────────────┤
│ snapshot_20250729_120001 │ SUCCESS │ 2.5GB │ 2025-07-29 │
│ snapshot_20250728_120001 │ SUCCESS │ 2.3GB │ 2025-07-28 │
│ snapshot_20250727_120001 │ FAILED  │ 0GB   │ 2025-07-27 │
╰──────────────────────────┴─────────┴───────┴────────────╯
```

**面板输出示例：**
```
╭───────────────────────────────────────────── 配置详情 ──────────────────────────────────────────────╮
│ 快照配置信息:                                                                                       │
│ • 集群地址: http://192.168.1.105:9200                                                               │
│ • 索引列表: index1, index2                                                                          │
│ • S3存储桶: my-bucket                                                                               │
│ • 存储库名称: my-repo                                                                               │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Syslog 格式 (LOG_FORMAT=syslog)

```
<134>Jul 30 11:24:56 snapshot: Starting snapshot creation
<134>Jul 30 11:24:56 snapshot: Snapshot configuration | snapshot_cluster=['http://192.168.1.105:9200'] | indices=['index1', 'index2'] | s3_bucket=my-bucket | repository=my-repo
<134>Jul 30 11:24:56 snapshot: Snapshot created successfully | snapshot_name=snapshot_20250730_112456
```

## 使用方法

### 基本日志调用

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

# 简单日志
logger.info("Starting operation")
logger.error("Operation failed")

# 结构化日志（支持额外字段）
logger.info("Snapshot configuration", 
    snapshot_cluster=["http://localhost:9200"],
    indices=["index1", "index2"],
    s3_bucket="my-bucket"
)

logger.error("Failed to create snapshot", 
    error="Connection timeout",
    retry_count=3
)
```

### 支持的日志级别

- `logger.debug()`: 调试信息
- `logger.info()`: 一般信息
- `logger.warning()`: 警告信息
- `logger.error()`: 错误信息

### Console 格式特有功能

Console 格式使用 Rich 库提供了额外的美观输出功能：

```python
# 成功/错误/警告消息
logger.print_success("操作成功完成")
logger.print_error("操作失败")
logger.print_warning("需要注意的警告")

# 表格输出
snapshots_data = [
    {"name": "snapshot_1", "status": "SUCCESS", "size": "2.5GB"},
    {"name": "snapshot_2", "status": "FAILED", "size": "0GB"},
]
columns = [
    ("快照名称", "name", "cyan"),
    ("状态", "status", "green"),
    ("大小", "size", "blue"),
]
logger.print_table("快照列表", snapshots_data, columns)

# 面板输出
content = "配置信息:\n• 集群: localhost:9200\n• 索引: index1, index2"
logger.print_panel(content, title="配置详情", style="blue")
```

## 日志格式规范

### Plain 格式标准

Plain 格式遵循以下标准：

1. **时间戳格式**: `YYYY-MM-DD HH:MM:SS`
2. **日志级别**: `INFO`, `WARNING`, `ERROR`, `DEBUG`
3. **消息格式**: 
   - 简单消息：`消息内容`
   - 结构化消息：`消息内容 | key1=value1 | key2=value2`

**示例：**
```
2025-07-29 12:00:00 INFO Starting snapshot creation
2025-07-29 12:00:01 INFO Snapshot configuration | snapshot_cluster=['http://192.168.1.105:9200'] | indices=['index1', 'index2']
2025-07-29 12:00:02 ERROR Failed to create snapshot | error=Connection timeout | retry_count=3
```

### 结构化字段命名规范

1. **使用下划线命名法**: `snapshot_name`, `user_id`, `ip_address`
2. **布尔值使用 `is_` 前缀**: `is_successful`, `is_retry`
3. **计数使用 `count` 后缀**: `deleted_count`, `retry_count`
4. **时间使用 `duration` 或 `timestamp`**: `duration_ms`, `created_timestamp`
5. **错误信息使用 `error` 字段**: `error=Connection timeout`

### 常见日志场景

#### 1. 用户操作日志
```python
logger.info("User successfully logged in", user_id=12345, ip="192.168.1.1")
logger.info("User logged out", user_id=12345, session_duration=3600)
```

#### 2. 系统操作日志
```python
logger.info("Snapshot backup completed", 
    snapshot_name="backup_20250729_120001",
    size_gb=2.5,
    duration_seconds=120,
    indices_count=10
)
```

#### 3. 错误日志
```python
logger.error("Failed to connect to Elasticsearch", 
    host="192.168.1.100",
    port=9200,
    error="Connection timeout",
    retry_count=3
)
```

#### 4. 性能指标日志
```python
logger.info("Operation completed", 
    operation="snapshot_creation",
    duration_ms=1500,
    success=True,
    items_processed=1000
)
```

## 最佳实践

### 1. 使用结构化日志

```python
# 推荐：使用结构化字段
logger.info("User action", 
    user_id=12345,
    action="login",
    ip_address="192.168.1.100"
)

# 不推荐：字符串拼接
logger.info(f"User {user_id} performed {action} from {ip_address}")
```

### 2. 错误日志包含上下文

```python
try:
    # 操作代码
    pass
except Exception as e:
    logger.error("Operation failed", 
        operation="snapshot_creation",
        error=str(e),
        config_file="config.yaml"
    )
```

### 3. 性能指标日志

```python
logger.info("Operation completed", 
    operation="snapshot_creation",
    duration_ms=1500,
    success=True,
    items_processed=1000
)
```

### 4. 日志级别使用原则

- **DEBUG**: 详细的调试信息，仅在开发环境使用
- **INFO**: 一般信息，记录重要的业务操作
- **WARNING**: 警告信息，可能的问题但不影响主要功能
- **ERROR**: 错误信息，操作失败但程序可以继续运行
- **CRITICAL**: 严重错误，程序无法继续运行

## 日志采集器集成

### ELK Stack (Elasticsearch, Logstash, Kibana)

JSON 格式的日志可以直接被 Logstash 解析：

```ruby
# logstash.conf
input {
  file {
    path => "/path/to/logs/*.log"
    codec => json
  }
}

filter {
  # 自动解析 JSON 字段
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "elasticsearch-snapshot-logs"
  }
}
```

### Syslog 集成

Syslog 格式的日志可以直接发送到系统日志服务：

```bash
# 使用 logger 命令测试
logger -p local0.info "Test message from elasticsearch-snapshot"

# 配置 rsyslog 接收日志
# /etc/rsyslog.d/elasticsearch-snapshot.conf
local0.* /var/log/elasticsearch-snapshot.log
```

### 纯文本格式集成

纯文本格式适合简单的日志收集和管道处理：

```bash
# 使用 grep 过滤
grep "snapshot_name" /var/log/elasticsearch-snapshot.log

# 使用 awk 提取字段
awk -F'|' '{print $2}' /var/log/elasticsearch-snapshot.log

# 重定向到其他工具
./elasticsearch-snapshot | tee /var/log/elasticsearch-snapshot.log
```

### Prometheus + Grafana

可以提取数值字段作为指标：

```python
logger.info("Snapshot metrics", 
    snapshot_size_gb=2.5,
    duration_seconds=120,
    indices_count=10
)
```

### Fluentd

```xml
<!-- fluent.conf -->
<source>
  @type tail
  path /path/to/logs/*.log
  format json
  tag elasticsearch.snapshot
</source>

<match elasticsearch.snapshot>
  @type elasticsearch
  host localhost
  port 9200
  index_name elasticsearch-snapshot-logs
</match>
```

## 故障排除

### 1. 日志不显示

检查环境变量设置：
```bash
echo $LOG_LEVEL
echo $LOG_FORMAT
```

### 2. JSON 格式错误

确保 JSON 字段值是可序列化的：
```python
# 正确
logger.info("Data", value=123, text="hello")

# 错误（包含不可序列化对象）
logger.info("Data", obj=some_object)
```

### 3. 性能问题

对于高频日志，考虑使用异步日志记录器或批量处理。 