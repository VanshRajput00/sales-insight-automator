# Lead Engineer Note: main.py is intentionally thin — it is the application
# shell, not the business logic. It wires together config, middleware, and
# routers. This pattern means any module can be swapped without touching this file.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.routers.upload import router as upload_router  # noqa: E402

load_dotenv()  # Reads .env before anything else touches os.environ

# --- App Instantiation ---
app = FastAPI(
    title="Sales Insight Automator API",
    description=(
        "Upload sales CSVs and receive AI-generated summaries. "
        "Built with FastAPI for auto-generated OpenAPI docs and high async throughput."
    ),
    version="1.0.0",
    contact={
        "name": "Engineering Team",
        "email": "engineering@yourcompany.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# --- CORS Middleware ---
# Lead Engineer Note: CORS is configured here at the app boundary, not inside
# individual routes. The ALLOWED_ORIGINS env var lets us set
# "http://localhost:3000" in dev and "https://yourdomain.com" in prod
# without touching code.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Route Registration ---
app.include_router(upload_router)


# --- Root Redirect ---
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Sales Insight Automator API is running.",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
