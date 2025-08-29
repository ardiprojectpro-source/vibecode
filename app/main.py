from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from .models import Job, Outputs, ModelsCache, ModelInfo
from . import openrouter, pipeline

app = FastAPI(title="Faceless ATM MVP")

models_cache = ModelsCache()
JOBS: Dict[str, Job] = {}


class JobCreate(BaseModel):
    url: str
    language: str
    niche: str
    persona: str
    originality_level: int = 3
    target_duration_min: int
    model_selected: Optional[str] = None


class OutputsModel(BaseModel):
    summary_points: List[str] = []
    outline: List[str] = []
    script_text: str = ""
    titles: List[str] = []
    description: str = ""
    keywords: List[str] = []
    timestamps: List[str] = []


class JobResponse(BaseModel):
    id: str
    status: str
    outputs: OutputsModel


@app.get("/models", response_model=List[ModelInfo])
async def get_models(refresh: bool = False) -> List[ModelInfo]:
    if refresh or not models_cache.is_valid():
        models_cache.update(await openrouter.fetch_models())
    return models_cache.models


@app.post("/jobs", response_model=JobResponse)
async def create_job(job_in: JobCreate, background_tasks: BackgroundTasks):
    if not job_in.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        url=job_in.url,
        language=job_in.language,
        niche=job_in.niche,
        persona=job_in.persona,
        originality_level=job_in.originality_level,
        target_duration_min=job_in.target_duration_min,
        model_selected=job_in.model_selected,
    )
    JOBS[job_id] = job
    # Placeholder transcript retrieval
    transcript = ""
    background_tasks.add_task(pipeline.process_job, job, transcript, job.model_selected or "openrouter/auto")
    return JobResponse(id=job.id, status=job.status, outputs=OutputsModel(**job.outputs.__dict__))


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(id=job.id, status=job.status, outputs=OutputsModel(**job.outputs.__dict__))
