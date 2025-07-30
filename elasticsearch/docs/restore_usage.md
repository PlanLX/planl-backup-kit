# Elasticsearch Restore 使用指南

## 概述

`restore.py` 提供了从S3存储库恢复Elasticsearch快照的功能，参考了 `snapshot.py` 的结构设计。

## 功能特性

- 从S3存储库恢复快照
- 支持环境变量配置
- 结构化日志记录
- 错误处理和重试机制
- 支持多种日志格式（JSON、Plain、Console、Syslog）

## 环境变量配置

### 必需环境变量

```bash
# Elasticsearch 配置
SNAPSHOT_HOSTS=http://localhost:9200          # 快照集群地址
RESTORE_HOSTS=http://localhost:9200           # 恢复集群地址
ES_REPOSITORY_NAME=my-repo                    # 存储库名称
ES_INDICES=index1,index2                      # 要恢复的索引

# S3 配置
S3_BUCKET_NAME=my-bucket                      # S3存储桶名称
S3_REGION=us-east-1                          # AWS区域
AWS_ACCESS_KEY_ID=your-access-key            # AWS访问密钥
AWS_SECRET_ACCESS_KEY=your-secret-key        # AWS秘密密钥

# 快照名称（通过环境变量或命令行参数提供）
SNAPSHOT_NAME=snapshot_20250730_120000
```

### 可选环境变量

```bash
# 日志配置
LOG_LEVEL=INFO                                # 日志级别
LOG_FORMAT=console                           # 日志格式 (json, plain, console, syslog)

# 认证配置
RESTORE_USERNAME=elastic                      # 恢复集群用户名
RESTORE_PASSWORD=password                     # 恢复集群密码
RESTORE_VERIFY_CERTS=true                     # 验证SSL证书

# 超时配置
SNAPSHOT_TIMEOUT=300                         # 操作超时时间（秒）
```

## 使用方法

### 1. 直接运行脚本

```bash
# 使用环境变量指定快照名称
export SNAPSHOT_NAME=snapshot_20250730_120000
python restore.py

# 使用命令行参数指定快照名称
python restore.py snapshot_20250730_120000
```

### 2. 使用模块方式运行

```bash
# 使用main.py
python main.py restore snapshot_20250730_120000

# 使用模块方式
python -m src.cli.main restore snapshot_20250730_120000
```

### 3. 使用安装后的脚本

```bash
# 安装后使用
es-backup restore snapshot_20250730_120000
```

## 代码示例

### 基本使用

```python
import asyncio
from restore import RestoreManager

async def restore_snapshot():
    # 创建恢复管理器
    manager = RestoreManager()
    
    # 恢复快照
    result = await manager.restore_snapshot("snapshot_20250730_120000")
    
    if result["success"]:
        print(f"快照恢复成功: {result['snapshot_name']}")
    else:
        print(f"快照恢复失败: {result['error']}")

# 运行
asyncio.run(restore_snapshot())
```

### 列出可用快照

```python
import asyncio
from restore import RestoreManager

async def list_snapshots():
    manager = RestoreManager()
    snapshots = await manager.list_snapshots()
    
    print("可用快照:")
    for snapshot in snapshots:
        print(f"- {snapshot['snapshot']} ({snapshot['state']})")

asyncio.run(list_snapshots())
```

### 获取快照状态

```python
import asyncio
from restore import RestoreManager

async def get_snapshot_status():
    manager = RestoreManager()
    status = await manager.get_snapshot_status("snapshot_20250730_120000")
    
    print(f"快照状态: {status['state']}")
    print(f"开始时间: {status['start_time']}")
    print(f"结束时间: {status['end_time']}")

asyncio.run(get_snapshot_status())
```

## 日志输出示例

### Console 格式

```
2025-07-30 13:45:00 INFO Starting snapshot restore | snapshot_name=snapshot_20250730_120000
2025-07-30 13:45:01 INFO Restore configuration | restore_cluster=['http://localhost:9200'] | indices=['index1', 'index2'] | s3_bucket=my-bucket | repository=my-repo
2025-07-30 13:45:02 INFO Snapshot restored successfully | snapshot_name=snapshot_20250730_120000
```

### JSON 格式

```json
{"timestamp": "2025-07-30T13:45:00.123Z", "level": "INFO", "logger": "restore", "message": "Starting snapshot restore", "snapshot_name": "snapshot_20250730_120000"}
{"timestamp": "2025-07-30T13:45:01.124Z", "level": "INFO", "logger": "restore", "message": "Restore configuration", "restore_cluster": ["http://localhost:9200"], "indices": ["index1", "index2"], "s3_bucket": "my-bucket", "repository": "my-repo"}
{"timestamp": "2025-07-30T13:45:02.125Z", "level": "INFO", "logger": "restore", "message": "Snapshot restored successfully", "snapshot_name": "snapshot_20250730_120000"}
```

## 错误处理

### 常见错误

1. **快照不存在**
   ```
   ValueError: Snapshot 'non_existent_snapshot' does not exist
   ```

2. **连接失败**
   ```
   ConnectionError: Failed to connect to Elasticsearch: Connection timeout
   ```

3. **权限错误**
   ```
   AuthenticationError: Invalid credentials for Elasticsearch
   ```

4. **S3访问错误**
   ```
   S3Error: Access denied to bucket 'my-bucket'
   ```

### 错误恢复

- 检查网络连接
- 验证Elasticsearch集群状态
- 确认S3存储桶权限
- 检查快照名称是否正确

## 最佳实践

### 1. 环境配置

- 使用环境变量而不是硬编码配置
- 为不同环境使用不同的配置文件
- 定期轮换AWS密钥

### 2. 监控和日志

- 启用结构化日志记录
- 监控恢复操作的性能
- 设置适当的日志级别

### 3. 安全考虑

- 使用IAM角色而不是硬编码密钥
- 启用SSL/TLS加密
- 限制网络访问

### 4. 性能优化

- 选择合适的快照大小
- 在低峰期进行恢复操作
- 监控集群资源使用情况

## 故障排除

### 检查配置

```bash
# 验证环境变量
env | grep -E "(SNAPSHOT|RESTORE|ES_|S3_|AWS_)"

# 测试Elasticsearch连接
curl -X GET "http://localhost:9200/_cluster/health"
```

### 检查日志

```bash
# 查看详细日志
LOG_LEVEL=DEBUG python restore.py snapshot_name

# 使用JSON格式便于分析
LOG_FORMAT=json python restore.py snapshot_name
```

### 验证快照

```bash
# 列出存储库中的快照
curl -X GET "http://localhost:9200/_snapshot/my-repo/_all"
```

## 与snapshot.py的对比

| 特性 | snapshot.py | restore.py |
|------|-------------|------------|
| 主要功能 | 创建快照 | 恢复快照 |
| 配置来源 | SNAPSHOT_HOSTS | RESTORE_HOSTS |
| 操作模式 | 写入操作 | 读取操作 |
| 清理功能 | 支持 | 不适用 |
| 工作流 | 创建+清理 | 仅恢复 |

## 总结

`restore.py` 提供了完整的Elasticsearch快照恢复功能，遵循了与 `snapshot.py` 相同的设计模式和代码结构，确保了项目的一致性和可维护性。 