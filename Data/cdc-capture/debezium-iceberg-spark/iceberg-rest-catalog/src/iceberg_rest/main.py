import uvicorn
from fastapi import FastAPI
from iceberg_rest.api.catalog_api import router as CatalogApiRouter
from iceberg_rest.exception import IcebergHTTPException, iceberg_http_exception_handler


def create_app():
    app = FastAPI()
    app.include_router(CatalogApiRouter)
    app.add_exception_handler(IcebergHTTPException, iceberg_http_exception_handler)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
