# Use Python 3.12 as base image
FROM python:3.12-slim AS builder

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

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml ./
COPY src/ ./src/
COPY snapshot.py ./

RUN uv sync

# Production stage
FROM python:3.12-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src ./src
COPY --from=builder /app/snapshot.py ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

RUN mkdir -p /app/config && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python", "snapshot.py"]

CMD ["--help"]