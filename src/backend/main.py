from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Desktop App Backend", version="0.1.0")
users = {"testuser": "password123", "mithish": "abc123"}

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


@app.post("/login")
def login(req: LoginRequest):
    print("Received:", req.dict())  # Debug line
    if req.username in users and users[req.username] == req.password:
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/signup")
def signup(req: LoginRequest):
    if req.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    users[req.username] = req.password
    return {"message": "Signup successful"}
