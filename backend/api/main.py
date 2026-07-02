import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routers import sync, tags

app = FastAPI(
    title="Business Central 365 Integration Gateway",
    description="Strictly READ-ONLY API gateway to pull data from BC 365 to ForgeBI Analytics",
    version="1.0.0"
)

# Enable CORS for frontend Dash App integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],  # Strictly enforce GET methods
    allow_headers=["*"],
)

# Include Routers
app.include_router(sync.router)
app.include_router(tags.router)

@app.get("/")
def read_root():
    return {
        "gateway": "Business Central API Gateway",
        "mode": "STRICTLY READ-ONLY",
        "status": "active"
    }

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
