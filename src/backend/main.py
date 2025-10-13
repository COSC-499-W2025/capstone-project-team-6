from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Desktop App Backend", version="0.1.0")

# Configure CORS for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Electron app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Backend is running"}


@app.get("/api/health")
def health_check():
    """API health check"""
    return {"status": "healthy"}
