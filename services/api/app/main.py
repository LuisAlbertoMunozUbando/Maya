from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    data_dir: Path = Path("/data")
    public_base_url: str = "http://127.0.0.1:8030"
    cors_origins: str = "http://localhost:3000,https://maya.albertomunoz.ai"
    cors_origin_regex: str = r"https://.*\.vercel\.app"
    maya_drive_folder_id: str | None = None


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
(settings.data_dir / "audio").mkdir(exist_ok=True)
(settings.data_dir / "exports").mkdir(exist_ok=True)


class Base(DeclarativeBase):
    pass


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_type: Mapped[str] = mapped_column(String, index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_variant: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    segments: Mapped[list["Segment"]] = relationship(back_populates="observation", cascade="all, delete-orphan")


class Segment(Base):
    __tablename__ = "segments"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observations.id"), index=True)
    start_seconds: Mapped[float] = mapped_column(Float, default=0)
    end_seconds: Mapped[float] = mapped_column(Float)
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcription_human: Mapped[str | None] = mapped_column(Text, nullable=True)
    phonetic_human: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    speaker: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="HUMAN_ANNOTATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    observation: Mapped[Observation] = relationship(back_populates="segments")
    inferences: Mapped[list["Inference"]] = relationship(cascade="all, delete-orphan")


class Inference(Base):
    __tablename__ = "inferences"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    segment_id: Mapped[str] = mapped_column(ForeignKey("segments.id"), index=True)
    task_type: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str] = mapped_column(String)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


engine = create_engine(f"sqlite:///{settings.data_dir / 'maya.sqlite3'}")
Base.metadata.create_all(engine)


class YoutubeObservationIn(BaseModel):
    url: HttpUrl
    title: str | None = None
    context_es: str | None = None
    location: str | None = None
    language_variant: str | None = None


class SegmentIn(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    transcription_human: str | None = None
    phonetic_human: str | None = None
    translation_es: str | None = None
    context_es: str | None = None
    speaker: str | None = None
    tags: list[str] = []


class InferenceIn(BaseModel):
    task_type: Literal["asr", "phonetic_transcription", "phonemic_transcription", "translation", "speech_translation", "language_id", "diarization", "embedding", "other"]
    model: str
    model_version: str | None = None
    output_text: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    provenance: dict = {}


app = FastAPI(title="Maya Multimodal Corpus API", version="0.1.1", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def obs_dict(o: Observation) -> dict:
    return {
        "id": o.id, "source_type": o.source_type, "source_url": o.source_url,
        "title": o.title, "context_es": o.context_es, "location": o.location,
        "language_variant": o.language_variant, "created_at": o.created_at,
        "metadata": o.metadata_json,
        "segments": [segment_dict(s) for s in o.segments],
    }


def segment_dict(s: Segment) -> dict:
    return {
        "id": s.id, "observation_id": s.observation_id,
        "start_seconds": s.start_seconds, "end_seconds": s.end_seconds,
        "audio_url": f"{settings.public_base_url}/api/v1/segments/{s.id}/audio" if s.audio_path else None,
        "transcription_human": s.transcription_human, "phonetic_human": s.phonetic_human,
        "translation_es": s.translation_es, "context_es": s.context_es,
        "speaker": s.speaker, "tags": s.tags, "status": s.status,
        "inferences": [{"id": i.id, "task_type": i.task_type, "model": i.model,
                        "model_version": i.model_version, "output_text": i.output_text,
                        "confidence": i.confidence, "provenance": i.provenance,
                        "created_at": i.created_at} for i in s.inferences],
    }


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "maya-api", "version": app.version}


@app.post("/api/v1/observations/youtube", status_code=201)
def create_youtube_observation(payload: YoutubeObservationIn):
    oid = f"obs_{uuid.uuid4().hex[:16]}"
    metadata = {}
    try:
        proc = subprocess.run(["yt-dlp", "--dump-single-json", "--skip-download", str(payload.url)], capture_output=True, text=True, timeout=60, check=True)
        raw = json.loads(proc.stdout)
        metadata = {k: raw.get(k) for k in ("id", "title", "channel", "duration", "thumbnail")}
    except Exception as exc:
        metadata = {"inspection_error": str(exc)}
    with Session(engine) as db:
        o = Observation(id=oid, source_type="youtube", source_url=str(payload.url), title=payload.title or metadata.get("title"), context_es=payload.context_es, location=payload.location, language_variant=payload.language_variant, metadata_json=metadata)
        db.add(o); db.commit(); db.refresh(o)
        return obs_dict(o)


@app.post("/api/v1/observations/capture", status_code=201)
def create_capture(audio: UploadFile = File(...), context_es: str | None = Form(None), transcription_human: str | None = Form(None), translation_es: str | None = Form(None), location: str | None = Form(None), language_variant: str | None = Form(None)):
    oid = f"obs_{uuid.uuid4().hex[:16]}"; sid = f"seg_{uuid.uuid4().hex[:16]}"
    suffix = Path(audio.filename or "capture.webm").suffix or ".webm"
    raw_path = settings.data_dir / "audio" / f"{sid}-original{suffix}"
    with raw_path.open("wb") as target: shutil.copyfileobj(audio.file, target)
    wav_path = settings.data_dir / "audio" / f"{sid}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(raw_path), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_path)], capture_output=True, timeout=120, check=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(wav_path)], capture_output=True, text=True, timeout=30, check=True)
    duration = float(probe.stdout.strip())
    with Session(engine) as db:
        o = Observation(id=oid, source_type="mobile_capture", context_es=context_es, location=location, language_variant=language_variant, metadata_json={"original_filename": audio.filename})
        s = Segment(id=sid, observation=o, start_seconds=0, end_seconds=duration, audio_path=str(wav_path), transcription_human=transcription_human, translation_es=translation_es, context_es=context_es)
        db.add(o); db.add(s); db.commit(); db.refresh(o)
        return obs_dict(o)


@app.post("/api/v1/observations/{observation_id}/segments", status_code=201)
def create_segment(observation_id: str, payload: SegmentIn):
    if payload.end_seconds <= payload.start_seconds: raise HTTPException(400, "end_seconds must be greater than start_seconds")
    with Session(engine) as db:
        o = db.get(Observation, observation_id)
        if not o: raise HTTPException(404, "Observation not found")
        sid = f"seg_{uuid.uuid4().hex[:16]}"; audio_path = None
        if o.source_type == "youtube" and o.source_url:
            work = settings.data_dir / "audio" / f"{sid}-source.%(ext)s"
            try:
                subprocess.run(["yt-dlp", "-f", "bestaudio/best", "-o", str(work), o.source_url], capture_output=True, timeout=300, check=True)
                source = next((settings.data_dir / "audio").glob(f"{sid}-source.*"))
                wav = settings.data_dir / "audio" / f"{sid}.wav"
                subprocess.run(["ffmpeg", "-y", "-ss", str(payload.start_seconds), "-to", str(payload.end_seconds), "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)], capture_output=True, timeout=120, check=True)
                source.unlink(missing_ok=True); audio_path = str(wav)
            except Exception as exc:
                raise HTTPException(502, f"Could not extract YouTube audio segment: {exc}") from exc
        s = Segment(id=sid, observation=o, start_seconds=payload.start_seconds, end_seconds=payload.end_seconds, audio_path=audio_path, transcription_human=payload.transcription_human, phonetic_human=payload.phonetic_human, translation_es=payload.translation_es, context_es=payload.context_es, speaker=payload.speaker, tags=payload.tags)
        db.add(s); db.commit(); db.refresh(s); return segment_dict(s)


@app.post("/api/v1/segments/{segment_id}/inferences", status_code=201)
def add_inference(segment_id: str, payload: InferenceIn):
    with Session(engine) as db:
        s = db.get(Segment, segment_id)
        if not s: raise HTTPException(404, "Segment not found")
        i = Inference(id=f"inf_{uuid.uuid4().hex[:16]}", segment_id=segment_id, **payload.model_dump())
        db.add(i); db.commit(); db.refresh(s); return segment_dict(s)


@app.get("/api/v1/observations")
def list_observations():
    with Session(engine) as db:
        return [obs_dict(o) for o in db.scalars(select(Observation).order_by(Observation.created_at.desc())).all()]


@app.get("/api/v1/observations/{observation_id}")
def get_observation(observation_id: str):
    with Session(engine) as db:
        o = db.get(Observation, observation_id)
        if not o: raise HTTPException(404, "Observation not found")
        return obs_dict(o)


@app.get("/api/v1/segments/{segment_id}/audio")
def get_audio(segment_id: str):
    with Session(engine) as db:
        s = db.get(Segment, segment_id)
        if not s or not s.audio_path: raise HTTPException(404, "Audio not found")
        p = Path(s.audio_path)
        if not p.exists(): raise HTTPException(404, "Audio file missing")
        return FileResponse(p, media_type="audio/wav", filename=f"{segment_id}.wav")


@app.get("/api/v1/export/jsonl")
def export_jsonl():
    path = settings.data_dir / "exports" / "maya-corpus.jsonl"
    with Session(engine) as db, path.open("w", encoding="utf-8") as f:
        for o in db.scalars(select(Observation)).all():
            for s in o.segments:
                f.write(json.dumps({"observation": {"id": o.id, "source_type": o.source_type, "source_url": o.source_url, "title": o.title, "language_variant": o.language_variant, "location": o.location}, "segment": segment_dict(s)}, ensure_ascii=False, default=str) + "\n")
    return FileResponse(path, media_type="application/x-ndjson", filename="maya-corpus.jsonl")