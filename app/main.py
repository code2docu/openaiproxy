from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import json
from uuid import UUID
from fastapi import Request


from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from starlette import status
from starlette.responses import JSONResponse

from processing import generate_markdown_doc

import requests
import logging

app = FastAPI()


class FunctionModel(BaseModel):
    name: str
    params: Optional[List[str]] = None
    returns: Optional[List[str]] = None
    calls: Optional[List[str]] = None

class FileModel(BaseModel):
    path: str
    language: str
    functions: Optional[List[FunctionModel]] = None

class FilesPayload(BaseModel):
    uuid: UUID
    promnt: str
    files: Optional[List[FileModel]] = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc} \nRequest body: {await request.body()}")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "validation_error", "detail": exc.errors()},
    )


@app.post("/python/analyze")
async def analyze(payload: FilesPayload, background_tasks: BackgroundTasks):
    try:
        received_uuid = payload.uuid
        recived_promnt = payload.promnt
        data = {
            "uuid": str(payload.uuid),
            "files": [file.dict() for file in payload.files]
        }

        background_tasks.add_task(generate_markdown_doc, data, str(received_uuid), str(recived_promnt))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok", "uuid": str(received_uuid)}
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error in /python/analyze: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "detail": str(e)}
        )
