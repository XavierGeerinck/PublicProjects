# iceberg-rest-catalog

> Original: https://github.com/binayakd/iceberg-rest-catalog & https://github.com/bitsondatadev/iceberg-rest-catalog

Pythonic Iceberg REST Catalog

## Build a docker image

**Base -** Supports SQLite backend only.

```
docker build . \
--target=prod \
--build-arg BASE_IMAGE=python:3.11-slim \
-t iceberg-rest-base
```

**Postgres -** Supports Postgres and SQLite backends.

```
docker build . \
--target=prod \
--build-arg EXTRAS=postgres \
--build-arg BASE_IMAGE=python:3.11-slim \
-t iceberg-rest-postgres
```

**MySQL -** Supports MySQL and SQLite backends.

```
docker build . \
--target=prod \
--build-arg EXTRAS=mysql \
--build-arg BASE_IMAGE=python:3.11 \
-t iceberg-rest-mysql
```

**Full -** Supports SQLite, Postgres, and MySQL backends.

```
docker build . \
--target=prod \
--build-arg EXTRAS='postgres mysql' \
--build-arg BASE_IMAGE=python:3.11 \
-t iceberg-rest-full
```

**Dev -** Supports SQLite, postgres, and MySQL backends. Includes all extra python packages and testing utilities.

```
docker build . \
--target=dev \
--build-arg BASE_IMAGE=python:3.11 \
-t iceberg-rest-dev
```

## Run the REST Catalog API server

```
docker run --rm -it -p 8000:8000 iceberg-rest-[base/postgres/mysql/full/dev]
```

Go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to inspect the OpenAPI documentation.

## Notes

- Currently the REST catalog saves metadata in the local filesystem (under the `/tmp/warehouse/` directory)
  This can be made configurable in the future.
- The Postgres and SQLite backends can be used from a slim python image but the MySQL backend requires the full size python base image.
