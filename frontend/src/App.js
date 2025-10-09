import { useState, useRef, useEffect } from "react";
import "@/App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // Poll for job status
  useEffect(() => {
    if (!jobId) return;

    const pollStatus = async () => {
      try {
        const response = await axios.get(`${API}/status/${jobId}`);
        setStatus(response.data);

        // Stop polling if completed or failed
        if (response.data.status === "completed" || response.data.status === "failed") {
          return;
        }
      } catch (err) {
        console.error("Error fetching status:", err);
      }
    };

    // Poll every 2 seconds
    const interval = setInterval(pollStatus, 2000);
    pollStatus(); // Initial call

    return () => clearInterval(interval);
  }, [jobId]);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setStatus(null);
      setJobId(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setJobId(response.data.job_id);
      setUploading(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
      setUploading(false);
    }
  };

  const handleDownload = async () => {
    if (!jobId) return;

    try {
      const response = await axios.get(`${API}/download/${jobId}`, {
        responseType: "blob",
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", status?.filename?.replace(/\.[^/.]+$/, "") + "_processed.zip");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Download failed. Please try again.");
    }
  };

  const handleReset = () => {
    setFile(null);
    setJobId(null);
    setStatus(null);
    setError(null);
    setUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getProgressColor = () => {
    if (status?.status === "failed") return "bg-red-500";
    if (status?.status === "completed") return "bg-green-500";
    return "bg-blue-500";
  };

  const getStatusIcon = () => {
    if (status?.status === "completed") return "✓";
    if (status?.status === "failed") return "✗";
    return "⟳";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            🎵 Audio to MIDI Converter
          </h1>
          <p className="text-xl text-purple-200">
            Separate audio into stems, convert each to MIDI & MusicXML
          </p>
        </div>

        {/* Main Card */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
            {!jobId ? (
              /* Upload Section */
              <div className="space-y-6">
                <div className="text-center">
                  <div className="mb-6">
                    <label
                      htmlFor="file-upload"
                      className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-purple-300 rounded-xl cursor-pointer hover:border-purple-400 hover:bg-white/5 transition-all duration-300"
                    >
                      <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <svg
                          className="w-16 h-16 mb-4 text-purple-300"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                          />
                        </svg>
                        <p className="mb-2 text-lg font-semibold text-purple-200">
                          {file ? file.name : "Click to upload audio file"}
                        </p>
                        <p className="text-sm text-purple-300">
                          MP3, WAV, FLAC, OGG, M4A
                        </p>
                      </div>
                      <input
                        id="file-upload"
                        type="file"
                        className="hidden"
                        accept=".mp3,.wav,.flac,.ogg,.m4a"
                        onChange={handleFileSelect}
                        ref={fileInputRef}
                      />
                    </label>
                  </div>

                  {error && (
                    <div className="mb-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200">
                      {error}
                    </div>
                  )}

                  <button
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-4 px-8 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 shadow-lg"
                  >
                    {uploading ? (
                      <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Uploading...
                      </span>
                    ) : (
                      "Start Processing"
                    )}
                  </button>
                </div>

                {/* Info Section */}
                <div className="mt-8 p-6 bg-white/5 rounded-xl border border-white/10">
                  <h3 className="text-lg font-semibold text-purple-200 mb-3">What this app does:</h3>
                  <ul className="space-y-2 text-purple-100">
                    <li className="flex items-start">
                      <span className="text-pink-400 mr-2">•</span>
                      <span>Separates audio into individual instrument stems (vocals, drums, bass, guitar, piano, etc.)</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-pink-400 mr-2">•</span>
                      <span>Converts each stem to MIDI format with accurate note detection</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-pink-400 mr-2">•</span>
                      <span>Generates MusicXML files for music notation software</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-pink-400 mr-2">•</span>
                      <span>Packages everything into a convenient ZIP download</span>
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              /* Processing Status Section */
              <div className="space-y-6">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-20 h-20 mb-4 rounded-full bg-purple-500/20 text-4xl">
                    {getStatusIcon()}
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">
                    {status?.status === "completed" ? "Processing Complete!" : 
                     status?.status === "failed" ? "Processing Failed" :
                     "Processing Your Audio..."}
                  </h2>
                  <p className="text-purple-200">{status?.filename}</p>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-purple-200">
                    <span>Progress</span>
                    <span>{status?.progress || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full ${getProgressColor()} transition-all duration-500 ease-out`}
                      style={{ width: `${status?.progress || 0}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-purple-300 text-center mt-2">
                    {status?.message}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4 mt-8">
                  {status?.status === "completed" && (
                    <button
                      onClick={handleDownload}
                      className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg"
                    >
                      Download ZIP
                    </button>
                  )}
                  <button
                    onClick={handleReset}
                    className="flex-1 bg-white/10 hover:bg-white/20 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 border border-white/20"
                  >
                    Process Another File
                  </button>
                </div>

                {status?.status === "processing" && (
                  <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg text-blue-200 text-sm text-center">
                    ⏱️ This may take several minutes depending on the audio length
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-purple-300">
          <p className="text-sm">Powered by Demucs (stem separation) & Basic Pitch (MIDI conversion)</p>
        </div>
      </div>
    </div>
  );
}

export default App;
