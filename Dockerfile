# cache dependencies
FROM python:3.13 AS python_cache
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/venv
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

WORKDIR /cache/
COPY pyproject.toml uv.lock ./
# RUN python -m venv /venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# build and start
FROM python:3.13-slim AS build
EXPOSE 80
WORKDIR /app
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=python_cache /venv /venv
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    strawberry export-schema main > schema.graphql
ENTRYPOINT [ "./entrypoint.sh" ]
