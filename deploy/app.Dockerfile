# Stage 1: install dependencies (cached unless lockfile changes)
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS deps
WORKDIR /opt/fast-soy-admin
COPY pyproject.toml uv.lock uv.toml ./
RUN uv sync --frozen --no-dev --no-install-project --extra ocr

# Stage 2: copy app source and run
FROM deps AS runtime
COPY . .
COPY .env.docker .env
ENV LANG=zh_CN.UTF-8
EXPOSE 9999
CMD ["uv", "run", "run.py"]
