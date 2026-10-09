from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings
from app.api.routes import hirisplex_results, plex34_structure, vcf

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="API for HIrisPlex-S and PLEX-34 phenotypic modeling"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vcf.router)
app.include_router(plex34_structure.router)
app.include_router(hirisplex_results.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HIrisPlex-S API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}
