Sales Insight Automator 🚀
An end-to-end AI-powered enterprise application that ingests CSV sales data, generates executive summaries using Gemini LLMs, and delivers responsive HTML reports via email.

⚡ Quick Start (The One Command)
Unpack or clone the repository.
Setup environment variables:
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY, SENDER_EMAIL, and SENDER_PASSWORD
Lift the infrastructure:
docker-compose up --build
Open the frontend: http://localhost:3000
🏗️ Architecture Stack
The project consists of three main orchestrated components:

Component	Technology	Description
Frontend	Next.js (Node 18), Tailwind v4, Framer Motion	Drag & drop UI with beautiful animations. Deployed as a standalone 150MB optimized image.
Backend	FastAPI, Python 3.11, Pandas	High-performance async API processing CSVs and directing AI flow. Run non-root for security.
Email Service	aiosmtplib	Non-blocking async SMTP integration for delivering executive reports.
🔒 Security & Orchestration highlights
Multi-Stage Docker Builds: Lean, production-ready images (frontend reduced from 1.2GB → 150MB by leveraging Next.js standalone output).
Non-Root Execution: Backend container explicitly drops privileges to appuser (UID/GID) to prevent host-level escalation.
Docker Compose Healthchecks: Guarantee service ordering (sia-frontend waits for sia-backend to start).
CI/CD Built-in: GitHub actions .github/workflows/main.yml automatically lints, type-checks, and validates Docker builds on every PR/push to main.
📡 API Reference
Method	Endpoint	Description
POST	/api/v1/upload	Multipart upload (CSV + email). Returns metrics + AI brief.
GET	/api/v1/health	Liveness probe (used by Docker Compose).
GET	/docs	Interactive Swagger API documentation.
📁 Project Structure
sales-insight-automator/
├── backend/          # FastAPI application (processor, router, services)
├── frontend/         # Next.js React Application
├── data/             # CSV sample data
├── .github/          # CI/CD Workflows
└── docker-compose.yml
