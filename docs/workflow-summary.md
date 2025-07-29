# Docker 构建工作流总结

## 概述

我们为 PlanL Backup Kit 项目创建了一个智能的 Docker 镜像自动构建工作流，该工作流能够根据代码变更的目录，自动构建和推送相应的 Docker 镜像。

## 创建的文件

### 1. GitHub Actions 工作流
- **`.github/workflows/docker-build.yml`**: 主要的 Docker 构建工作流文件

### 2. Docker 配置文件
- **`elasticsearch/Dockerfile`**: 已存在，Elasticsearch 服务的 Docker 配置
- **`mysql/Dockerfile`**: 新创建，MySQL 服务的 Docker 配置
- **`postgresql/Dockerfile`**: 新创建，PostgreSQL 服务的 Docker 配置
- **`mongodb/Dockerfile`**: 新创建，MongoDB 服务的 Docker 配置

### 3. Python 项目配置
- **`mysql/pyproject.toml`**: MySQL 服务的 Python 项目配置
- **`postgresql/pyproject.toml`**: PostgreSQL 服务的 Python 项目配置
- **`mongodb/pyproject.toml`**: MongoDB 服务的 Python 项目配置

### 4. 源代码结构
为每个数据库服务创建了基本的源代码结构：
```
{service}/
├── src/
│   ├── __init__.py
│   └── cli/
│       ├── __init__.py
│       └── main.py
├── main.py
├── pyproject.toml
├── uv.lock
└── Dockerfile
```

### 5. 文档
- **`docs/docker-workflow.md`**: 详细的 Docker 工作流文档
- **`docs/workflow-summary.md`**: 本总结文档

### 6. 测试脚本
- **`scripts/test-docker-builds.sh`**: Bash 版本的测试脚本
- **`scripts/test-docker-builds.ps1`**: PowerShell 版本的测试脚本

## 工作流特性

### 智能变更检测
- 自动检测哪些数据库服务目录发生了变化
- 只构建发生变更的服务镜像
- 支持 Git 差异比较

### 多平台支持
- 支持 AMD64 和 ARM64 架构
- 使用 Docker Buildx 进行多平台构建
- 优化构建缓存

### 自动化标签
- 分支标签：`main`, `develop`
- PR 标签：`pr-{number}`
- 语义化版本：`v1.0.0`, `v1.0`
- 提交 SHA：`main-{sha}`

### 安全特性
- 使用非 root 用户运行容器
- 多阶段构建减少镜像大小
- 仅推送非 PR 事件的镜像
- GitHub Token 身份验证

## 触发条件

工作流会在以下情况下自动触发：

1. **推送代码**到 `main` 或 `develop` 分支
2. **创建 Pull Request** 到 `main` 或 `develop` 分支
3. **修改以下路径的文件**：
   - `elasticsearch/**`
   - `mysql/**`
   - `postgresql/**`
   - `mongodb/**`
   - `.github/workflows/docker-build.yml`

## 镜像命名规范

镜像将推送到 GitHub Container Registry，命名格式为：
```
ghcr.io/{repository}/{service}
```

例如：
- `ghcr.io/your-org/planl-backup-kit/elasticsearch`
- `ghcr.io/your-org/planl-backup-kit/mysql`
- `ghcr.io/your-org/planl-backup-kit/postgresql`
- `ghcr.io/your-org/planl-backup-kit/mongodb`

## 使用方法

### 1. 自动构建
工作流会在代码推送或 PR 创建时自动运行，无需手动干预。

### 2. 本地测试
使用提供的测试脚本验证 Docker 构建：

```bash
# Linux/macOS
./scripts/test-docker-builds.sh

# Windows PowerShell
.\scripts\test-docker-builds.ps1
```

### 3. 手动构建
```bash
# 构建单个服务
docker build -t planl-backup-kit-elasticsearch ./elasticsearch
docker build -t planl-backup-kit-mysql ./mysql
docker build -t planl-backup-kit-postgresql ./postgresql
docker build -t planl-backup-kit-mongodb ./mongodb
```

## 扩展指南

### 添加新的数据库服务

1. 创建新的服务目录（如 `redis/`）
2. 添加 `Dockerfile`
3. 创建 `pyproject.toml` 和源代码结构
4. 更新工作流文件中的路径检测
5. 添加对应的构建任务

### 自定义配置

可以修改以下配置：
- 支持的平台架构
- 缓存策略
- 标签规则
- 构建参数
- 触发条件

## 监控和调试

### 查看工作流状态
- 在 GitHub 仓库的 Actions 标签页查看工作流运行状态
- 查看构建日志和错误信息

### 常见问题
1. **构建失败**: 检查 Dockerfile 语法和依赖
2. **推送失败**: 确认 GitHub Token 权限
3. **缓存问题**: 清除 GitHub Actions 缓存
4. **多平台构建失败**: 检查 Dockerfile 兼容性

## 下一步

1. **测试工作流**: 推送代码到仓库测试工作流是否正常工作
2. **配置权限**: 确保 GitHub Token 有推送镜像的权限
3. **监控构建**: 观察首次构建的日志和结果
4. **优化配置**: 根据实际使用情况调整构建参数

## 相关链接

- [Docker 工作流详细文档](docker-workflow.md)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Buildx 文档](https://docs.docker.com/buildx/)
- [GitHub Container Registry 文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)