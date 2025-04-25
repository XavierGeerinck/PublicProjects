from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

ERROR = "error"
CODE = "code"
MESSAGE = "message"


class IcebergHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        error_msg = {ERROR: {CODE: status_code, MESSAGE: detail}}
        super().__init__(status_code=status_code, detail=error_msg)

    def to_json_response(self):
        return JSONResponse(status_code=self.status_code, content=self.detail)


def iceberg_http_exception_handler(request: Request, exc: IcebergHTTPException):
    return exc.to_json_response()
