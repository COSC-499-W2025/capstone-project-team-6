# Mining Digital Work Artifacts: Research on 10 Recommended LLM + RAG Model Stacks  
*Prepared for the Mining Digital Work Artifacts project – Milestone 1 (Parsing, Analysis & Design Phase)*  

---

## Overview

This research document evaluates **ten Large Language Model (LLM)** stacks suitable for a **local-first RAG (Retrieval Augmented Generation)** system with cloud fallback options. The goal is to power accurate extraction, classification, and summarization of digital work artifacts from zipped project archives, while complying with stringent privacy and data consent requirements.

The models are divided into two groups:

- **Local Models (5 options)** — can run fully offline on a laptop or workstation
- **Cloud-based Models (5 options)** — require external API access but deliver the highest accuracy and the most advanced reasoning, including coding and multimodal capabilities

Each model stack includes a brief description of the **generator LLM**, **embedding model**, and **optional reranker**, along with specific **project fit**, **technical rationale**, and **integration context**.

---

## 1. Local Models (Offline, Installed Weights)

These models are recommended when a user does not grant consent to upload file contents to external services. All of them support **100% local inference** on consumer hardware (CPU or GPU), and can be quantized for memory efficiency.

---

### 1.1 Llama 3.1 8B Instruct (Local)

**Highlights**: Latest generation Meta model; optimized for code, reasoning, and multilingual tasks  
**Embedding**: `nomic-embed-text-v1.5`  
**Reranker**: `bge-reranker-v2-m3` (optional for high precision)

#### Why choose it:
- Great balance between **model quality** and **compute footprint**
- Excellent for **parsing** and **summarizing** heterogeneous artifacts: code, notes, logs, docs  
- 8B size works well with **llama.cpp**, **vLLM**, or local GPU (8–12 GB)  
- Community ecosystem support is thriving  
- Strong multilingual & English code handling

#### Ideal use cases:
- Extracting skills, frameworks, and coding languages from zipped folders  
- Generating résumé-ready summaries for top projects  
- Classifying code and non-code contributions for student portfolios  

---

### 1.2 Qwen 2.5 7B Instruct (Local)

**Highlights**: Long context handling (up to ~131K tokens)  
**Embedding**: `jina-embeddings-v3` (8192 tokens)  
**Reranker**: `bge-reranker-v2-m3`

#### Why choose it:
- Leading **long-context** performance among compact models  
- Handles large logs, commit histories, or README docs in one shot  
- Great for mining years of projects and assembling **chronological contribution timelines**

#### Ideal use cases:
- Full-text ingestion of loosely organized work archives  
- Chunk-free RAG when working with fewer but large input files  
- Multi-language reports and long commit message summaries  

---

### 1.3 Mistral 7B Instruct v0.3 (Local)

**Highlights**: Apache-2 licensed, fast CPU inference, accepts function calling  
**Embedding**: `nomic-embed-text-v1.5`  
**Reranker**: `bge-reranker-v2-m3`

#### Why choose it:
- Small and fast—but still powerful for **structured outputs** and tool calling  
- Easy to integrate with Python backends using `llama-cpp-python` or `transformers`  
- Fully open weights (no usage limits or telemetry concerns)

#### Ideal use cases:
- Lightweight student or freelancer use cases  
- Clear and deterministic extraction + API-style JSON structure  
- Runs comfortably on machines without dedicated GPUs  

---

### 1.4 DeepSeek-Coder V2 16B (Local)

**Highlights**: State-of-the-art for code-specific reasoning  
**Embedding**: `jina-embeddings-v3`  
**Reranker**: `bge-reranker-v2-m3`

#### Why choose it:
- Superb understanding of code semantics and docs  
- Better for code-heavy archives and technical users  
- Handles code explanations, refactor summaries, and diff generation

#### Ideal use cases:
- Analyzing Git repositories and GitHub-style commit messages  
- Identifying per-file contributions on collaborative repos  
- Auto-generating pull request summaries and changelog items  

---

### 1.5 StarCoder2-15B (Local)

**Highlights**: Industry-grade multilingual code understanding (600+ languages)  
**Embedding**: `nomic-embed-text-v1.5`  
**Reranker**: `bge-reranker-v2-m3`

#### Why choose it:
- Designed for **mixed language repositories** and software portfolios  
- Fill-in-the-middle support for partial code repair or reconstruction  
- Supports great code summaries, framework detection, and module classification

#### Ideal use cases:
- Student portfolios involving multiple programming languages  
- Extracting test-vs-source statistics from nested repos  
- Writing technical project descriptions for job applications  

---

## 2. Cloud Models (External API, Highest Accuracy)

These models are ideal when the user **opts in to cloud processing** and needs best-in-class reasoning, code understanding, and multimodal support (e.g., screenshot, PDF, diagram parsing).

---

### 2.1 OpenAI GPT-5

**Highlights**: Strongest OpenAI model for code, structured outputs, and reasoning  
**Embeddings**: OpenAI `text-embedding-3-large`  
**Reranker**: Optional, not required if using native Retrieval

#### Why choose it:
- Best general-purpose performance among cloud LLMs  
- Excellent at extracting soft skills, roles, and impact for résumé bullets  
- Mature function calling + JSON schema support makes integration easy  
- Handles cross-file context for contributions smoothly

#### Ideal use cases:
- High-stakes analysis: submission to employers, public portfolio sites  
- Rich narrative writing: “what I learned,” “role in team,” “impact”  
- Complex chain-of-thought classification using many files, timelines, and notes  

---

### 2.2 Anthropic Claude Sonnet 4.5

**Highlights**: Advanced reasoning + coding + multi-step agentic control  
**Embeddings**: Cohere, OpenAI, or cross-vendor  
**Reranker**: Cohere Rerank or local BGE

#### Why choose it:
- Outstanding multi-subtask orchestration (agents)  
- Follows rules and pipelines reliably  
- Excellent ethics safety layer (important for personal data mining)

#### Ideal use cases:
- Multi-stage analysis pipelines (chunk → classify → score → summarize)  
- Polished portfolio website generation with narratively coherent results  
- Natural-language processing of git and changelog contents  

---

### 2.3 Google Gemini 2.5 Pro

**Highlights**: Multimodal: understands text, code, diagrams, design screenshots  
**Embeddings**: Vertex AI text-embeddings or OpenAI embeddings  
**Reranker**: BGE or Cloud-native

#### Why choose it:
- Multi-modal understanding: PDF, images, docs, wireframes  
- Integrates easily into a Google workflow (Colab, GCS, Vertex)  
- Handles extremely long contexts (videos, long PDFs)

#### Ideal use cases:
- Users who include PDFs, Figma drafts, screenshots in project folders  
- Reconstructing evolution of visual design along with code or doc changes  
- Cloud-run pipelines that scale up for batch uploads

---

### 2.4 Cohere Command A (03-2025 Edition)

**Highlights**: Enterprise-grade RAG, 256K context window  
**Embeddings**: Cohere `embed-v3`  
**Reranker**: Cohere `rerank-v3`

#### Why choose it:
- Purpose-built for structured RAG extraction and accurate ranking  
- Long context supports fewer chunks, more stable results  
- Company-grade privacy API with great speed and pricing tiers

#### Ideal use cases:
- High-volume ingestion (hundreds of projects at once)  
- Third-party resumés or dashboards built at scale  
- Teams building productized analytics or SaaS dashboards  

---

### 2.5 Amazon Nova Premier (AWS Bedrock)

**Highlights**: Native multimodal enterprise model from AWS  
**Embeddings**: Titan Embeddings or cross-provider  
**Reranker**: Amazon Bedrock Knowledge Base Rerank

#### Why choose it:
- One-stop integration with AWS services: S3, DynamoDB, IAM  
- Supports rich vision+text extraction for mixed media files  
- Guardrails and compliance for teams working with real users

#### Ideal use cases:
- Enterprise workspaces with AWS adoption  
- Projects where zipped folders include mix of code, docs, and images  
- Need for private, tightly controlled in-region deployments  

---

## 3. Integration Summary

Below is a consolidated comparison to help you pick a stack depending on user consent, performance needs, and offline requirements.

| User Scenario | Best Model Stack (Local) | Best Model Stack (Cloud) |
|---------------|--------------------------|--------------------------|
| No cloud upload allowed | Llama 3.1 8B or Mistral 7B | N/A |
| Code-heavy projects | DeepSeek-Coder V2 or StarCoder2 | GPT-5 or Claude Sonnet |
| Long text logs / no chunking | Qwen 2.5 | Cohere Command A |
| Design+code artifacts | Llama 3.1 or StarCoder2 | Gemini 2.5 Pro or Nova Premier |
| Resume and storytelling | Llama 3.1 | GPT-5 or Claude Sonnet |
| Batch project ingestion | Qwen 2.5 | Cohere Command A |

---

## 4. Technical Notes (All Models)

- **RAG Flow**: `zip → parse → metadata → chunk → embed → retrieve → rerank → LLM → structured JSON`
- **Vector DB**: Locally (SQLite + FAISS, LanceDB) or cloud (Pinecone, Chroma Cloud)
- **User Consent**: Must gate uploads before any cloud ops
- **Fallback (Offline)**: Local LLM ingestion + deterministic parse/tagging fallback
- **Deletion Safety**: Index file-to-record map and remove on-demand

---

## 5. Next Steps

- Choose 1 local + 1 cloud stack for prototype
- Implement CLI with privacy/consent flags
- Build `rag_pipeline.py` with:
  - Pluggable generator
  - Pluggable embedding backend
  - Configs saved in local `.json` file

---