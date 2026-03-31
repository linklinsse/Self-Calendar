FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

# Setup a non-root user
# RUN groupadd --system --gid 999 nonroot \
#  && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY ./app /work/app
COPY uv.lock /work/
COPY pyproject.toml /work/

WORKDIR /work

# Disable development dependencies
ENV UV_NO_DEV=1

RUN uv sync --locked

# Use the non-root user to run our application
# USER nonroot

CMD ["uv", "run", "fastapi", "run", "app/app.py", "--port", "8082"]