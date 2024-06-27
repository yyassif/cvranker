from starlette.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    # Any Properietary Domain
]

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # orgins should be replaced
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )