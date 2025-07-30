# PlanLX Elasticsearch Backup Kit

Elasticsearch备份和恢复工具包，支持S3存储。

## 功能特性

- 🔄 **备份和恢复**: 支持Elasticsearch索引的完整备份和恢复
- ☁️ **S3集成**: 无缝集成AWS S3存储
- 🧹 **快照清理**: 独立的快照清理工具，支持多种清理策略
- 🛡️ **安全认证**: 支持Elasticsearch和AWS的身份验证
- 📊 **状态监控**: 实时查看备份和恢复状态
- 🎯 **灵活配置**: 支持多种配置文件格式（YAML、JSON、环境变量）
- 🚀 **异步操作**: 高性能的异步操作支持
- 🎨 **美观界面**: 使用Rich库提供美观的命令行界面

## 快速开始

### 安装

使用uv安装依赖：

```bash
# 安装开发依赖
uv sync --dev

# 或者安装生产依赖
uv sync
```

### 创建配置文件

```bash
# 创建示例配置文件
python main.py init --output config.yaml

# 或者使用JSON格式
python main.py init --output config.json --format json
```

### 配置说明

编辑生成的配置文件，更新以下关键信息：

```yaml
elasticsearch:
  src_hosts: ["http://localhost:9200"]  # 源集群地址
  dest_hosts: ["http://localhost:9200"]  # 目标集群地址
  repository_name: "my-s3-repository"    # S3存储库名称
  indices: ["my-index-1", "my-index-2"]  # 要备份的索引

s3:
  bucket_name: "my-elasticsearch-backups"  # S3存储桶名称
  base_path: "elasticsearch-backups"       # S3基础路径
  region: "us-east-1"                      # AWS区域

aws_credentials:
  access_key: "your-access-key"            # AWS访问密钥
  secret_key: "your-secret-key"            # AWS秘密密钥
  region: "us-east-1"                      # AWS区域
```

### 使用示例

#### 创建备份

```bash
# 使用配置文件
python main.py -c config.yaml backup

# 使用环境变量
python main.py backup
```

#### 恢复备份

```bash
# 恢复指定快照
python main.py -c config.yaml restore snapshot-2024-01-15T10-30-00
```

#### 列出快照

```bash
# 查看所有可用快照
python main.py -c config.yaml list-snapshots
```

#### 查看快照状态

```bash
# 查看特定快照状态
python main.py -c config.yaml status snapshot-2024-01-15T10-30-00
```

#### 清理快照

```bash
# 清理指定快照
python main.py -c config.yaml cleanup --names snapshot-2024-01-15T10-30-00,snapshot-2024-01-14T09-15-00

# 清理所有快照
python main.py -c config.yaml cleanup --all

# 清理匹配模式的快照
python main.py -c config.yaml cleanup --pattern "snapshot-2024*"

# 清理早于指定日期的快照
python main.py -c config.yaml cleanup --older-than "2024-01-01"

# 模拟运行（预览将要删除的快照）
python main.py -c config.yaml cleanup --all --dry-run
```

#### 独立清理工具

项目还提供了一个独立的清理工具：

```bash
# 使用独立清理工具
python cleanup.py --all

# 或者使用命令行工具
es-cleanup --all
```

更多清理工具的使用方法，请参考 [清理工具文档](docs/cleanup.md)。

## 环境变量配置

您也可以使用环境变量进行配置：

```bash
# Elasticsearch配置
export BACKUP_ELASTICSEARCH__SRC_HOSTS='["http://localhost:9200"]'
export BACKUP_ELASTICSEARCH__DEST_HOSTS='["http://localhost:9200"]'
export BACKUP_ELASTICSEARCH__REPOSITORY_NAME="my-repository"
export BACKUP_ELASTICSEARCH__INDICES='["index1", "index2"]'

# S3配置
export BACKUP_S3__BUCKET_NAME="my-backups"
export BACKUP_S3__REGION="us-east-1"

# AWS凭证
export BACKUP_AWS_CREDENTIALS__ACCESS_KEY="your-access-key"
export BACKUP_AWS_CREDENTIALS__SECRET_KEY="your-secret-key"
export BACKUP_AWS_CREDENTIALS__REGION="us-east-1"
```

## 命令行选项

### 全局选项

- `-c, --config`: 配置文件路径
- `--log-level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `-v, --verbose`: 启用详细日志

### 子命令

- `init`: 创建示例配置文件
- `backup`: 执行备份操作
- `restore <snapshot_name>`: 执行恢复操作
- `list-snapshots`: 列出所有快照
- `status <snapshot_name>`: 查看快照状态
- `cleanup`: 清理快照（支持多种清理策略）

## 开发

### 项目结构

```
src/planlx_backup_kit/
├── __init__.py          # 包初始化
├── cli/                 # 命令行界面
│   ├── __init__.py
│   └── main.py         # CLI主入口
├── core/               # 核心功能
│   ├── __init__.py
│   ├── backup.py       # 备份功能
│   └── restore.py      # 恢复功能
├── models/             # 数据模型
│   ├── __init__.py
│   └── config.py       # 配置模型
└── utils/              # 工具函数
    ├── __init__.py
    ├── config_loader.py # 配置加载
    └── logging.py      # 日志工具
```

### 代码格式化

```bash
# 使用ruff格式化代码
uv run ruff format .

# 使用ruff检查代码
uv run ruff check .

# 类型检查
uv run mypy src/
```

### 测试

```bash
# 运行测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=src/planlx_backup_kit
```

## 依赖项

- **elasticsearch**: Elasticsearch Python客户端
- **boto3**: AWS SDK for Python
- **pydantic**: 数据验证和设置管理
- **click**: 命令行界面框架
- **rich**: 美观的终端输出
- **python-dotenv**: 环境变量管理

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 支持

如果您遇到问题或有任何疑问，请创建GitHub Issue。
