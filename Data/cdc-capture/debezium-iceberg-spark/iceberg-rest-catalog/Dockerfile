########################################################################################

ARG BASE_IMAGE=python:3.12
FROM ${BASE_IMAGE} AS runtime-base
WORKDIR /home/iceberg/iceberg_rest

# Make sure terminal does not wait at a prompt
ENV DEBIAN_FRONTEND=nonintercative

# Install curl for healthcheck
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create iceberg user
RUN groupadd iceberg && \
    useradd -rms /bin/bash -g iceberg iceberg && \
    chown -R iceberg:iceberg /home/iceberg

# Create a directory for the sqlite database
RUN mkdir -p /tmp/warehouse && \
    chown -R iceberg:iceberg /tmp/warehouse

########################################################################################

FROM runtime-base AS build-base

ARG POETRY_VERSION=1.8.3
ARG POETRY_HOME="/opt/poetry"

# Use bash shell
SHELL ["/bin/bash", "-c"]

# Make sure terminal does not wait at a prompt
ENV DEBIAN_FRONTEND=nonintercative

# Install system packages
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    libmariadb-dev-compat \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
ENV POETRY_HOME=${POETRY_HOME} \
    POETRY_VERSION=${POETRY_VERSION}
RUN curl -sSL https://install.python-poetry.org/ | python3

# Add Poetry to the path
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy in the config files
COPY pyproject.toml poetry.toml ./

########################################################################################

FROM build-base AS build-prod
ARG EXTRAS=base

# Install the dependencies first so they are cached
RUN poetry install --no-root --extras "${EXTRAS}"

########################################################################################

FROM build-base AS build-dev

# Install the dependencies first so they are cached
RUN poetry install --no-root --with dev --all-extras

########################################################################################

FROM runtime-base AS prod

# Add the virtualenv from the build-prod stage into the runtime image
COPY --from=build-prod /home/iceberg/iceberg_rest/.venv /home/iceberg/iceberg_rest/.venv
ENV PATH="/home/iceberg/iceberg_rest/.venv/bin:$PATH"

# Give the iceberg user ownership of the iceberg_rest directory
RUN chown -R iceberg:iceberg /home/iceberg/iceberg_rest

# Switch to iceberg user
USER iceberg

# Add the source code
COPY pyproject.toml ./
COPY src/ src/
COPY README.md README.md

# Install the source package
RUN pip install . --no-deps

# Serve the app in production mode
CMD ["uvicorn", "src.iceberg_rest.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Healthcheck
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=5 \
    CMD curl -f  http://localhost:8000/v1/config || exit 1

########################################################################################

FROM runtime-base AS dev

# Make sure terminal does not wait at a prompt
# Make sure python does not write pyc files, i.e. pytest_cache
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1

# Install system packages required for dev.
# Git is required to run pre-commit during ci.
RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Add the virtualenv from the build-prod stage into the runtime image
COPY --from=build-dev /home/iceberg/iceberg_rest/.venv /home/iceberg/iceberg_rest/.venv
ENV PATH="/home/iceberg/iceberg_rest/.venv/bin:$PATH"

# Give the iceberg user ownership of the iceberg_rest directory
RUN chown -R iceberg:iceberg /home/iceberg/iceberg_rest

# Switch to iceberg user
USER iceberg

# Add the source code
COPY pyproject.toml poetry.lock poetry.toml ./
COPY src/ src/
COPY tests/ tests/
COPY README.md README.md

# Install the source package
RUN pip install . --no-deps

# Serve the app in development mode
CMD ["uvicorn", "src.iceberg_rest.main:app", "--host",  "0.0.0.0", "--port", "8000", "--reload"]

########################################################################################
