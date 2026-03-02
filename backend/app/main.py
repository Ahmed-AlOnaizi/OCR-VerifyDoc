import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

app = FastAPI(title="Document Verification Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    import app.models  # noqa: F401 — ensure models are registered

    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Seed sample users on first run
    from app.seed import seed_users

    seed_users()


# Import and include routers after app is created
from app.api.users import router as users_router  # noqa: E402
from app.api.documents import router as documents_router  # noqa: E402
from app.api.jobs import router as jobs_router  # noqa: E402

app.include_router(users_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/reset")
def reset_data():
    """Delete all documents, jobs, and uploaded files. Re-seeds users."""
    import shutil
    from app.database import SessionLocal
    from app.models.document import Document
    from app.models.verification_job import VerificationJob

    db = SessionLocal()
    try:
        db.query(VerificationJob).delete()
        db.query(Document).delete()
        db.commit()
    finally:
        db.close()

    # Clear uploaded files
    if os.path.exists(settings.UPLOAD_DIR):
        shutil.rmtree(settings.UPLOAD_DIR)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    return {"status": "reset complete"}
