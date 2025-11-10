# Llama Stack Local Setup Guide

This guide walks through setting up Llama Stack with Ollama for local LLM inference and embeddings.

Note that this setup is to ensure everything is locally made, Models, database,etc...

## Prerequisites

- Docker and Docker Compose installed
- At least 16GB RAM (8GB minimum) 
- ~5GB free disk space for models
- Internet connection for downloading models

## Architecture

Below is the current architecture and will become more complex in the future with the vector database and 2 regualr databases being add, CLI and output system
```
┌─────────────────────────────────────────────┐
│         Docker Compose Network              │
│                                             │
│  ┌──────────────────┐                       │
│  │  Llama Stack     │                       │
│  │  (Port 8000)     │                       │
│  └────────┬─────────┘                       │
│           │                                 │
│           ▼                                 │
│  ┌──────────────────┐                       │
│  │     Ollama       │                       │
│  │  (Port 11434)    │                       │
│  │                  │                       │
│  │ Models:          │                       │
│  │ • mistral:latest │                       │
│  │ • nomic-embed-   │                       │
│  │   text:latest    │                       │
│  └──────────────────┘                       │
└─────────────────────────────────────────────┘
```

## Files Created

1. `docker-compose.llama-stack.yml` - Docker orchestration
2. `config.yaml` - Application configuration

Note: There is a seperate docker file for now for testing purposes but will be combined with the original docker file in a seperate issue

## Setup Steps

**This assumes you are already in the appropiate virtual environment**

### Step 1: Navigate to Scripts Directory
```bash
cd scripts
```

### Step 2: Start Ollama Only (First Time)
```bash
# Start only Ollama to pull models first
docker-compose -f docker-compose.llama-stack.yml up -d ollama
```

Wait ~30 seconds for Ollama to be ready.

### Step 3: Verify Ollama is Running
```bash
docker exec -it ollama ollama list
```

Expected output: Empty list or existing models.

### Step 4: Pull Required Models

**Pull Mistral (Chat/Completion Model - ~4.1GB):**
```bash
docker exec -it ollama ollama pull mistral
```

Wait for download to complete (progress bar will show).

**Pull Nomic Embed Text (Embedding Model - ~274MB):**
```bash
docker exec -it ollama ollama pull nomic-embed-text
```

### Step 5: Verify Models Are Installed
```bash
docker exec -it ollama ollama list
```

Expected output:
```
NAME                    ID              SIZE
mistral:latest          ...             4.1 GB
nomic-embed-text:latest ...             274 MB
```

### Step 6: Start Full Stack
```bash
# Start all services (Ollama + Llama Stack)
docker-compose -f docker-compose.llama-stack.yml up -d
```

### Step 7: Verify Services Are Running

**Check container status:**
```bash
docker-compose -f docker-compose.llama-stack.yml ps
```

Expected output: Both `ollama` and `llama-stack` should be "Up" and healthy.

**Check Llama Stack logs:**
```bash
docker-compose -f docker-compose.llama-stack.yml logs -f llama-stack
```

Look for: `INFO ... Server started successfully` (or similar success message).

Press `Ctrl+C` to exit logs.

### Step 8: Test Llama Stack API

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

Expected: HTTP 200 response.

**Test models endpoint:**
```bash
curl http://localhost:8000/v1/models
```

Expected: JSON response listing available models.

## Current Configuration

### Models in Use

The models were changed from initially planned since they were not compatible with ollama provider

- **Chat Model:** `mistral:latest` (Mistral 7B Instruct)
- **Embedding Model:** `nomic-embed-text:latest` (768 dimensions)

### Ports Exposed

- `11434` - Ollama API
- `8000` - Llama Stack API

### Data Persistence

Models are persisted in Docker volume `ollama_data` - they won't need to be re-downloaded after container restarts.

## Changing Models

### To Use Different Chat Model

1. Pull new model:
```bash
   docker exec -it ollama ollama pull llama3.1:8b
```

2. Update `docker-compose.llama-stack.yml`:
```yaml
   - INFERENCE_MODEL=llama3.1:8b
```

3. Update `config.yaml`:
```yaml
   chat:
     model: "llama3.1:8b"
```

4. Restart:
```bash
   docker-compose -f docker-compose.llama-stack.yml restart llama-stack
```

### To Use Different Embedding Model

1. Pull new model:
```bash
   docker exec -it ollama ollama pull mxbai-embed-large
```

2. Update `docker-compose.llama-stack.yml`:
```yaml
   - EMBEDDING_MODEL=mxbai-embed-large:latest
   - EMBEDDING_DIMENSION=1024  # Update dimension!
```

3. Update `config.yaml`:
```yaml
   embedding:
     model: "mxbai-embed-large:latest"
     dimension: 1024  # Must match!
   
   database:
     vector_dimension: 1024  # Must match!
```

4. Restart:
```bash
   docker-compose -f docker-compose.llama-stack.yml restart llama-stack
```

**IMPORTANT:** Always update dimension in 3 places when changing embedding model!

## GPU Support (Optional)

If you have an NVIDIA GPU and nvidia-docker2 installed:

1. Uncomment the GPU section in `docker-compose.llama-stack.yml`:
```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
```

2. Restart services:
```bash
   docker-compose -f docker-compose.llama-stack.yml down
   docker-compose -f docker-compose.llama-stack.yml up -d
```

GPU acceleration significantly improves inference speed.

## Troubleshooting

### Llama Stack keeps restarting

**Check logs:**
```bash
docker-compose -f docker-compose.llama-stack.yml logs llama-stack
```

**Common issues:**
- Models not pulled yet → Pull models first (Step 4)
- Wrong model names → Use `ollama list` to verify names
- Ollama not ready → Wait longer or check Ollama logs

### Out of memory errors

- Stop other containers/applications
- Use smaller models (e.g., `llama3.2:3b`)
- Enable GPU support if available

### Connection refused errors

- Check if services are running: `docker ps`
- Verify ports not in use: `netstat -an | grep 8000`
- Check firewall settings

## Stopping Services

**Stop all services:**
```bash
docker-compose -f docker-compose.llama-stack.yml down
```

**Stop but keep containers:**
```bash
docker-compose -f docker-compose.llama-stack.yml stop
```

## Removing Everything (Clean Slate)

**Warning: This deletes downloaded models!**
```bash
docker-compose -f docker-compose.llama-stack.yml down -v
```

The `-v` flag removes volumes, including the `ollama_data` volume with your models.

## Quick Reference Commands
```bash
# Start services
docker-compose -f docker-compose.llama-stack.yml up -d

# Stop services
docker-compose -f docker-compose.llama-stack.yml down

# View logs
docker-compose -f docker-compose.llama-stack.yml logs -f

# Restart a service
docker-compose -f docker-compose.llama-stack.yml restart llama-stack

# List models in Ollama
docker exec -it ollama ollama list

# Pull a new model
docker exec -it ollama ollama pull <model-name>

# Remove a model
docker exec -it ollama ollama rm <model-name>
```

## Improvements

Once Llama Stack is running successfully,our next step si to
- connect the databases to docker
- connect the CLI to docker
