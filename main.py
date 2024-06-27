import logging
from logger import get_logger
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from middlewares.cors import add_cors_middleware
from modules.ranker.controller import ranker_router
from packages import handle_request_validation_error

# Load environment variables
load_dotenv()

# Set the logging level for all loggers to WARNING
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = get_logger(__name__)

def before_send(event, hint):
    # If this is a transaction event
    if event["type"] == "transaction":
        # And the transaction name contains 'healthz'
        if "healthz" in event["transaction"]:
            # Drop the event by returning None
            return None
    # For other events, return them as is
    return event


app = FastAPI()

add_cors_middleware(app)

app.include_router(ranker_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

handle_request_validation_error(app)

if __name__ == "__main__":
    # run main.py to debug backend
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5050, log_level="warning", access_log=False)
