from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database


app = FastAPI(title="Desktop App Backend", version="0.1.0")

# Configure CORS for Electron app


class LoginRequest(BaseModel):
    username: str
    password: str


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


@app.on_event("startup")
def startup() -> None:
    database.initialize()


@app.post("/login")
def login(req: LoginRequest):
    print("Received:", req.dict())  # Debug line
    if database.authenticate_user(req.username, req.password):
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/signup")
def signup(req: LoginRequest):
    try:
        database.create_user(req.username, req.password)
    except database.UserAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Signup successful"}
