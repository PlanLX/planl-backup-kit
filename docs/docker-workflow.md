# Docker 构建工作流

本文档描述了 PlanL Backup Kit 项目的 Docker 镜像自动构建工作流。

## 概述

项目使用 GitHub Actions 工作流来自动构建和推送 Docker 镜像。工作流会根据代码变更的目录，智能地只构建发生变化的服务镜像。

## 支持的数据库服务

- **Elasticsearch** (`elasticsearch/`)
- **MySQL** (`mysql/`)
- **PostgreSQL** (`postgresql/`)
- **MongoDB** (`mongodb/`)

## 工作流触发条件

工作流会在以下情况下触发：

1. **推送代码**到 `main` 或 `develop` 分支
2. **创建 Pull Request** 到 `main` 或 `develop` 分支
3. **修改以下路径的文件**：
   - `elasticsearch/**`
   - `mysql/**`
   - `postgresql/**`
   - `mongodb/**`
   - `.github/workflows/docker-build.yml`

## 工作流执行流程

### 1. 变更检测 (detect-changes)

工作流首先会检测哪些目录发生了变化：

- 比较当前提交与上一个提交的差异
- 检查各个数据库目录是否有文件变更
- 输出变更状态供后续任务使用

### 2. 条件构建

只有发生变更的目录才会触发对应的构建任务：

- `build-elasticsearch`: 构建 Elasticsearch 镜像
- `build-mysql`: 构建 MySQL 镜像
- `build-postgresql`: 构建 PostgreSQL 镜像
- `build-mongodb`: 构建 MongoDB 镜像

### 3. 镜像构建和推送

每个构建任务会：

- 设置 Docker Buildx
- 登录到 GitHub Container Registry (仅限非 PR 事件)
- 提取镜像元数据
- 构建多平台镜像 (linux/amd64, linux/arm64)
- 推送镜像到注册表 (仅限非 PR 事件)

### 4. 构建总结

最后会生成一个构建总结，显示：
- 检测到的变更
- 各服务的构建结果

## 镜像标签策略

镜像会根据以下规则自动生成标签：

- **分支标签**: `main`, `develop` 等
- **PR 标签**: `pr-{number}`
- **语义化版本**: `v1.0.0`, `v1.0` 等
- **提交 SHA**: `main-{sha}` 等

## 镜像命名规范

镜像名称格式：`ghcr.io/{repository}/{service}`

例如：
- `ghcr.io/your-org/planl-backup-kit/elasticsearch`
- `ghcr.io/your-org/planl-backup-kit/mysql`
- `ghcr.io/your-org/planl-backup-kit/postgresql`
- `ghcr.io/your-org/planl-backup-kit/mongodb`

## 缓存策略

工作流使用 GitHub Actions 缓存来加速构建：

- 构建缓存：`type=gha`
- 缓存模式：`mode=max`
- 支持跨运行缓存

## 安全特性

- 使用非 root 用户运行容器
- 多阶段构建减少镜像大小
- 仅推送非 PR 事件的镜像
- 使用 GitHub Token 进行身份验证

## 本地开发

### 构建单个镜像

```bash
# 构建 Elasticsearch 镜像
docker build -t planl-backup-kit-elasticsearch ./elasticsearch

# 构建 MySQL 镜像
docker build -t planl-backup-kit-mysql ./mysql

# 构建 PostgreSQL 镜像
docker build -t planl-backup-kit-postgresql ./postgresql

# 构建 MongoDB 镜像
docker build -t planl-backup-kit-mongodb ./mongodb
```

### 运行容器

```bash
# 运行 Elasticsearch 容器
docker run --rm planl-backup-kit-elasticsearch

# 运行 MySQL 容器
docker run --rm planl-backup-kit-mysql

# 运行 PostgreSQL 容器
docker run --rm planl-backup-kit-postgresql

# 运行 MongoDB 容器
docker run --rm planl-backup-kit-mongodb
```

## 故障排除

### 常见问题

1. **构建失败**: 检查 Dockerfile 语法和依赖
2. **推送失败**: 确认 GitHub Token 权限
3. **缓存问题**: 清除 GitHub Actions 缓存
4. **多平台构建失败**: 检查 Dockerfile 兼容性

### 调试步骤

1. 查看工作流日志
2. 检查变更检测输出
3. 验证 Dockerfile 语法
4. 测试本地构建

## 配置选项

### 环境变量

- `REGISTRY`: 容器注册表地址 (默认: ghcr.io)
- `IMAGE_NAME`: 镜像名称前缀 (默认: github.repository)

### 构建参数

- `PIP_INDEX_URL`: Python 包索引 URL
- `HTTP_PROXY`: HTTP 代理设置

## 扩展指南

### 添加新的数据库服务

1. 创建新的目录 (如 `redis/`)
2. 添加 Dockerfile
3. 创建基本的项目结构
4. 更新工作流文件中的路径检测
5. 添加对应的构建任务

### 自定义构建配置

可以修改工作流文件来自定义：

- 支持的平台架构
- 缓存策略
- 标签规则
- 构建参数

## 相关文件

- `.github/workflows/docker-build.yml`: 主工作流文件
- `*/Dockerfile`: 各服务的 Dockerfile
- `*/pyproject.toml`: Python 项目配置
- `*/main.py`: 应用入口点