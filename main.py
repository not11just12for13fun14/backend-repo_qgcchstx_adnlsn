import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Project, TuningJob

app = FastAPI(title="ArcynForge Backend", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "ArcynForge Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from ArcynForge backend API"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ----- Schema Introspection -----
class SchemaOut(BaseModel):
    name: str
    schema: Dict[str, Any]


@app.get("/schema")
def get_schema():
    """Expose JSON schemas for known models so external tools can inspect."""
    models = {
        "project": Project.model_json_schema(),
        "tuningjob": TuningJob.model_json_schema(),
    }
    return {"models": models}


# Utility functions

def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


# ----- Projects API -----
@app.get("/api/projects")
def list_projects(limit: Optional[int] = 50):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    docs = get_documents("project", {}, min(limit or 50, 200))
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return {"items": docs}


@app.post("/api/projects")
def create_project(project: Project):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    inserted_id = create_document("project", project)
    return {"id": inserted_id}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    doc = db["project"].find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


# ----- Tuning Jobs API -----
@app.get("/api/tuning-jobs")
def list_tuning_jobs(limit: Optional[int] = 50, project_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    filt: Dict[str, Any] = {}
    if project_id:
        filt["project_id"] = project_id
    docs = get_documents("tuningjob", filt, min(limit or 50, 200))
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return {"items": docs}


@app.post("/api/tuning-jobs")
def create_tuning_job(job: TuningJob, background_tasks: BackgroundTasks):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    data = job.model_dump()
    if not data.get("status"):
        data["status"] = "queued"
    inserted_id = create_document("tuningjob", data)

    # simulate async progression
    def _progress(job_id: str):
        try:
            from time import sleep
            db["tuningjob"].update_one({"_id": _oid(job_id)}, {"$set": {"status": "running"}})
            sleep(2)
            db["tuningjob"].update_one({"_id": _oid(job_id)}, {"$set": {"status": "completed"}})
        except Exception:
            try:
                db["tuningjob"].update_one({"_id": _oid(job_id)}, {"$set": {"status": "failed"}})
            except Exception:
                pass

    background_tasks.add_task(_progress, inserted_id)
    return {"id": inserted_id, "status": data.get("status", "queued")}


class StatusBody(BaseModel):
    status: str


@app.put("/api/tuning-jobs/{job_id}/status")
def update_tuning_job_status(job_id: str, body: StatusBody):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    res = db["tuningjob"].update_one({"_id": _oid(job_id)}, {"$set": {"status": body.status}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tuning job not found")
    doc = db["tuningjob"].find_one({"_id": _oid(job_id)})
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/api/tuning-jobs/{job_id}")
def get_tuning_job(job_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    doc = db["tuningjob"].find_one({"_id": _oid(job_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Tuning job not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
