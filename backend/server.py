from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import shutil
import asyncio
import subprocess
import tempfile
import zipfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create directories for file storage
UPLOADS_DIR = Path("/app/uploads")
PROCESSED_DIR = Path("/app/processed")
UPLOADS_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Define Models
class ProcessingJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    status: str  # pending, processing, completed, failed
    progress: int = 0
    message: str = ""
    output_file: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobStatus(BaseModel):
    id: str
    filename: str
    status: str
    progress: int
    message: str
    output_file: Optional[str] = None

# Processing function
async def process_audio_to_stems_midi(job_id: str, audio_path: Path, filename: str):
    """Process audio file: separate stems, convert to MIDI and MusicXML"""
    try:
        # Update job status to processing
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "processing",
                "progress": 10,
                "message": "Starting stem separation...",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Create work directory
        work_dir = PROCESSED_DIR / job_id
        work_dir.mkdir(exist_ok=True)
        stems_dir = work_dir / "stems"
        stems_dir.mkdir(exist_ok=True)
        
        # Step 1: Separate stems using Demucs
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "progress": 20,
                "message": "Separating audio into stems (this may take a few minutes)...",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Run Demucs separation
        demucs_output = work_dir / "demucs_output"
        demucs_cmd = [
            "/root/.venv/bin/python", "-m", "demucs",
            "-n", "htdemucs_6s",  # 6-stem model: drums, bass, other, vocals, guitar, piano
            "-o", str(demucs_output),
            str(audio_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *demucs_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Demucs failed: {stderr.decode()}")
        
        # Find the separated stems
        audio_name = audio_path.stem
        separated_dir = demucs_output / "htdemucs_6s" / audio_name
        
        if not separated_dir.exists():
            raise Exception("Stem separation output not found")
        
        # Get all stem files
        stem_files = list(separated_dir.glob("*.wav"))
        total_stems = len(stem_files)
        
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "progress": 50,
                "message": f"Found {total_stems} stems. Converting to MIDI...",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Step 2: Convert each stem to MIDI using basic-pitch
        midi_dir = work_dir / "midi"
        midi_dir.mkdir(exist_ok=True)
        musicxml_dir = work_dir / "musicxml"
        musicxml_dir.mkdir(exist_ok=True)
        
        for idx, stem_file in enumerate(stem_files):
            stem_name = stem_file.stem
            progress = 50 + int((idx / total_stems) * 40)
            
            await db.jobs.update_one(
                {"id": job_id},
                {"$set": {
                    "progress": progress,
                    "message": f"Converting {stem_name} to MIDI ({idx+1}/{total_stems})...",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Copy stem to stems directory
            shutil.copy(stem_file, stems_dir / f"{stem_name}.wav")
            
            # Convert to MIDI using basic-pitch
            midi_output_dir = midi_dir / stem_name
            midi_output_dir.mkdir(exist_ok=True)
            
            basic_pitch_cmd = [
                "basic-pitch",
                str(midi_output_dir),
                str(stem_file)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *basic_pitch_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Find the generated MIDI file and rename it
            midi_files = list(midi_output_dir.glob("*.mid"))
            if midi_files:
                midi_file = midi_files[0]
                final_midi = midi_dir / f"{stem_name}.mid"
                shutil.move(str(midi_file), str(final_midi))
                
                # Convert MIDI to MusicXML using music21
                try:
                    from music21 import converter
                    score = converter.parse(str(final_midi))
                    musicxml_file = musicxml_dir / f"{stem_name}.musicxml"
                    score.write('musicxml', fp=str(musicxml_file))
                except Exception as e:
                    logging.warning(f"MusicXML conversion failed for {stem_name}: {e}")
            
            # Clean up temp directory
            shutil.rmtree(midi_output_dir, ignore_errors=True)
        
        # Step 3: Create ZIP file
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "progress": 90,
                "message": "Creating download package...",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        zip_filename = f"{audio_name}_processed.zip"
        zip_path = work_dir / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add stems
            for stem_file in stems_dir.glob("*.wav"):
                zipf.write(stem_file, f"stems/{stem_file.name}")
            
            # Add MIDI files
            for midi_file in midi_dir.glob("*.mid"):
                zipf.write(midi_file, f"midi/{midi_file.name}")
            
            # Add MusicXML files
            for xml_file in musicxml_dir.glob("*.musicxml"):
                zipf.write(xml_file, f"musicxml/{xml_file.name}")
        
        # Update job as completed
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "message": "Processing complete! Your files are ready for download.",
                "output_file": zip_filename,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Clean up temporary files
        shutil.rmtree(demucs_output, ignore_errors=True)
        
    except Exception as e:
        logging.error(f"Processing failed for job {job_id}: {str(e)}")
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "message": f"Processing failed: {str(e)}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Audio to MIDI Converter API"}

@api_router.post("/upload")
async def upload_audio(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload audio file and start processing"""
    try:
        # Validate file type
        allowed_extensions = [".mp3", ".wav", ".flac", ".ogg", ".m4a"]
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id,
            filename=file.filename,
            status="pending",
            progress=0,
            message="File uploaded, waiting to process..."
        )
        
        # Save to database
        job_dict = job.model_dump()
        job_dict['created_at'] = job_dict['created_at'].isoformat()
        job_dict['updated_at'] = job_dict['updated_at'].isoformat()
        await db.jobs.insert_one(job_dict)
        
        # Save uploaded file
        upload_path = UPLOADS_DIR / f"{job_id}{file_ext}"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Start processing in background
        background_tasks.add_task(process_audio_to_stems_midi, job_id, upload_path, file.filename)
        
        return {"job_id": job_id, "message": "File uploaded successfully. Processing started."}
        
    except Exception as e:
        logging.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing status of a job"""
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**job)

@api_router.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download the processed ZIP file"""
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not job.get("output_file"):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    zip_path = PROCESSED_DIR / job_id / job["output_file"]
    
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=str(zip_path),
        filename=job["output_file"],
        media_type="application/zip"
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
