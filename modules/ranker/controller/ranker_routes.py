from typing import List

from logger import get_logger
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, HTTPException, UploadFile
from modules.ranker.ito.cvranker import CVRankerAssistant

ranker_router = APIRouter()
logger = get_logger(__name__)

@ranker_router.post(
    "/ranker/process",
    tags=["Ranker Assistant"],
)
async def ranker_process(
    files: List[UploadFile],
    job_description: str = Form(),
):
    print("Ranker process")
    print("job_description", job_description)
    print("files", files)
    try:
        cvranker_assistant = CVRankerAssistant(job_description=job_description, files=files)
        cvranker_assistant.check_input()
        output = await cvranker_assistant.process_assistant()
        return JSONResponse(
            status_code=200,
            content={ "output": output },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

