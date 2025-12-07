# mp3stemxml Setup Guide

## 🎵 **Overview**

**mp3stemxml** is an advanced audio processing tool that:
1. **Separates** MP3 files into individual stems (drums, bass, vocals, guitar, piano, other)
2. **Converts** each stem to MIDI notation
3. **Exports** MusicXML files for notation software
4. **Packages** everything in a downloadable ZIP file

---

## ✅ **Fixes Applied**

1. ✅ Renamed `server.txt` → `server.py` (backend now runnable)
2. ✅ Updated frontend `.env` to use localhost backend
3. ✅ Fixed React dependency conflicts (date-fns, react-day-picker)

---

## 📋 **Prerequisites**

### **System Requirements:**
- **Python 3.10+** (backend)
- **Node.js 18+** (frontend)
- **MongoDB** (running locally)
- **FFmpeg** (required for audio processing)
- **~10GB disk space** (for AI models)

### **Install FFmpeg (Windows):**
```powershell
# Option 1: Using Chocolatey
choco install ffmpeg

# Option 2: Download from https://ffmpeg.org/download.html
# Add to PATH manually
```

---

## 🚀 **Quick Start**

### **Step 1: Start MongoDB**

```powershell
# Option A: Local MongoDB service
mongod

# Option B: Docker
docker run -d -p 27017:27017 --name mp3stemxml-mongo mongo:latest
```

### **Step 2: Backend Setup**

```powershell
cd c:\Users\OGT\DoctrineForgedDesigns\EffortlessMetaphor\mp3stemxml\backend

# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\Activate.ps1

# Install dependencies (this will take a while - ~2-3 GB download)
pip install -r requirements.txt

# Start backend server
uvicorn server:app --reload --port 8000
```

**⏳ First Run Notes:**
- **Demucs model** (~300MB) will download on first use
- **Basic-pitch model** (~100MB) will download on first use
- Subsequent runs will be much faster!

### **Step 3: Frontend Setup** (New Terminal)

```powershell
cd c:\Users\OGT\DoctrineForgedDesigns\EffortlessMetaphor\mp3stemxml\frontend

# Install dependencies
npm install

# Start frontend
npm start
```

Frontend will open at: **http://localhost:3000**

---

## 🎼 **How to Use**

### **1. Upload Audio**
- Click "Choose File" or drag & drop an MP3/WAV file
- Max file size: ~50MB recommended
- Click "Upload & Process"

### **2. Processing Pipeline**
The backend will:
1. **Separate stems** (2-5 minutes depending on song length)
   - Uses Demucs `htdemucs_6s` model
   - Extracts: drums, bass, vocals, guitar, piano, other
2. **Convert to MIDI** (~1-2 minutes per stem)
   - Uses basic-pitch for audio-to-MIDI
3. **Export MusicXML** (notation format)
4. **Create ZIP package**

### **3. Download Results**
Once processing is complete:
- Click "Download Package"
- Get a ZIP file containing:
  - `stems/` - Individual audio stems (WAV files)
  - `midi/` - MIDI files for each stem
  - `musicxml/` - MusicXML notation files

---

## 📁 **Project Structure**

```
mp3stemxml/
├── backend/
│   ├── server.py          # FastAPI backend
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Backend config (MongoDB)
│   └── tests/            # Backend tests
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main upload/processing UI
│   │   └── components/   # UI components
│   ├── package.json      # Node dependencies
│   └── .env             # Frontend config
├── uploads/              # Temporary uploads
├── processed/            # Processing workspace
└── SETUP_GUIDE.md       # This file
```

---

## 🔧 **Configuration**

### **Backend `.env`**
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
```

### **Frontend `.env`**
```env
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
```

---

## 🎯 **What You Get**

### **Stems (Audio Files)**
- `drums.wav` - Drum track
- `bass.wav` - Bass line
- `vocals.wav` - Vocal track
- `guitar.wav` - Guitar parts
- `piano.wav` - Piano/keys
- `other.wav` - Everything else

### **MIDI Files**
- `drums.mid` - Drum notation
- `bass.mid` - Bass notation
- `vocals.mid` - Vocal melody
- `guitar.mid` - Guitar notation
- `piano.mid` - Piano notation
- `other.mid` - Other instruments

### **MusicXML Files**
- Import into **MuseScore**, **Sibelius**, **Finale**
- Edit notation, transpose, print scores
- Full musical notation with timing

---

## 🛠️ **Troubleshooting**

### **Backend Issues**

**Problem: ModuleNotFoundError for audio libraries**
```powershell
# Reinstall with all dependencies
pip install --upgrade -r requirements.txt
```

**Problem: FFmpeg not found**
```powershell
# Verify FFmpeg is installed
ffmpeg -version

# If not found, install via Chocolatey or download binary
```

**Problem: Demucs fails with CUDA errors**
- The backend uses CPU by default
- If you see GPU errors, it's safe to ignore (CPU will be used)

**Problem: MongoDB connection refused**
```powershell
# Start MongoDB
net start MongoDB

# Or check if running
Get-Service MongoDB
```

### **Frontend Issues**

**Problem: npm install fails**
```powershell
# Clear cache and reinstall
rm -r node_modules
rm package-lock.json
npm install
```

**Problem: Can't connect to backend**
- Verify backend is running at http://localhost:8000
- Check backend terminal for errors
- Test API directly: http://localhost:8000/api/status/test

### **Processing Issues**

**Problem: Processing takes too long**
- Normal processing time: 5-10 minutes for a 3-minute song
- CPU-only processing is slower than GPU
- Close other heavy applications

**Problem: Out of memory**
- Processing large files (>50MB) uses significant RAM
- Try processing shorter clips first
- Ensure at least 8GB RAM available

---

## 🚀 **Performance Tips**

### **Speed Up Processing:**
1. **Use shorter audio clips** for testing (30-60 seconds)
2. **Close unnecessary applications** (frees RAM)
3. **GPU acceleration** (if you have NVIDIA GPU):
   ```powershell
   # Install PyTorch with CUDA
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### **Better Results:**
- Use **high-quality source audio** (320kbps MP3 or WAV)
- Avoid heavily compressed/low-quality files
- Instrumental tracks work better than full mixes

---

## 📦 **AI Models Used**

### **Demucs (htdemucs_6s)**
- **Purpose:** Stem separation
- **Size:** ~300MB
- **Output:** 6 stems (drums, bass, vocals, guitar, piano, other)
- **Speed:** ~2-5 minutes per song (CPU)

### **Basic-Pitch**
- **Purpose:** Audio-to-MIDI conversion
- **Size:** ~100MB
- **Accuracy:** Best for monophonic/simple polyphonic audio
- **Speed:** ~30 seconds per stem

---

## 🎓 **Use Cases**

### **For Musicians:**
- Learn songs by isolating instruments
- Practice with isolated backing tracks
- Transcribe complex passages
- Create karaoke tracks (remove vocals)

### **For Producers:**
- Remix songs with separated stems
- Sample individual instruments
- Create mashups with clean stems
- Study arrangement techniques

### **For Music Students:**
- Analyze arrangements
- Study individual instrument parts
- Create sheet music from recordings
- Practice sight-reading with generated scores

---

## 🆘 **Need Help?**

If processing fails:

1. **Check backend logs** (terminal where uvicorn is running)
2. **Check job status** in MongoDB:
   ```javascript
   // MongoDB shell
   use test_database
   db.jobs.find().pretty()
   ```
3. **Try a shorter/simpler audio file** first
4. **Verify FFmpeg** is accessible: `ffmpeg -version`

---

## 🎉 **Ready to Start!**

Once both servers are running:
1. Open http://localhost:3000
2. Upload an MP3/WAV file
3. Wait for processing to complete (~5-10 minutes)
4. Download your stems + MIDI + MusicXML!

**Pro Tip:** Start with a 30-second audio clip to test the full pipeline before processing longer songs!
