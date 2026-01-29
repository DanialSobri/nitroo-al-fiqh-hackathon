from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import contract, regulation
from app.models.schemas import HealthResponse
from app.services.qdrant_service import qdrant_service

app = FastAPI(
    title="Shariah Compliance Checker API",
    description="AI-powered Shariah compliance checking system for Islamic contracts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "Content-Length"]
)

app.include_router(contract.router)
app.include_router(regulation.router)

@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Shariah Compliance Checker API",
        "version": "1.0.0",
        "endpoints": {
            "contracts": "/contracts",
            "regulations": "/regulations",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    health_info = qdrant_service.health_check()
    
    return HealthResponse(
        status="healthy" if health_info.get("connected") else "unhealthy",
        qdrant_connected=health_info.get("connected", False),
        collections=health_info.get("collections", {})
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
