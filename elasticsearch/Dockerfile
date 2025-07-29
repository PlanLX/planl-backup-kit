# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim as builder

ARG PIP_INDEX_URL
ARG HTTP_PROXY

# Set proxy and index
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTP_PROXY}
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV UV_DEFAULT_INDEX=${PIP_INDEX_URL}
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy

# 设置工作目录
WORKDIR /app

# 配置华为源
RUN sed -i 's@deb.debian.org@repo.huaweicloud.com@g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY main.py ./

# 使用 uv 安装依赖
RUN uv sync --frozen

# 生产阶段
FROM python:3.12-slim as production

# 设置工作目录
WORKDIR /app

# 配置华为源
RUN sed -i 's@deb.debian.org@repo.huaweicloud.com@g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 从构建阶段复制 Python 环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY --from=builder /app/src ./src
COPY --from=builder /app/main.py ./

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# 创建配置目录
RUN mkdir -p /app/config && chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 设置入口点
ENTRYPOINT ["python", "main.py"]

# 默认命令
CMD ["--help"]