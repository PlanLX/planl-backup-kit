# Use Python 3.12 as base image
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

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY main.py ./

# Install dependencies with uv
RUN uv sync

# Production stage
FROM python:3.12-slim as production

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/main.py ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Create config directory
RUN mkdir -p /app/config && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["python", "main.py"]

# Default command
CMD ["--help"]