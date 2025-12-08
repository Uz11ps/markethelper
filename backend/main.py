import uvicorn
from backend.app import create_app
from fastapi.middleware.cors import CORSMiddleware

app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # фронтенд
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
