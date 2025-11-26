#!/usr/bin/env python3
"""
Simple test to verify core functionality without full backend setup
"""

import os
import tempfile
import numpy as np
import wave
from pathlib import Path

def create_test_audio_file(duration=3, sample_rate=44100, frequency=440):
    """Create a short sine wave audio file for testing"""
    print(f"Creating test audio file: {duration}s sine wave at {frequency}Hz")
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(frequency * 2 * np.pi * t)
    
    # Convert to 16-bit integers
    wave_data = (wave_data * 32767).astype(np.int16)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())
    
    return temp_file.name

def test_audio_file_creation():
    """Test that we can create a valid audio file"""
    print("\n=== Testing Audio File Creation ===")
    try:
        audio_file = create_test_audio_file(duration=3)
        print(f"✅ Audio file created: {audio_file}")
        print(f"File size: {os.path.getsize(audio_file)} bytes")
        
        # Verify it's a valid WAV file
        with wave.open(audio_file, 'r') as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            frames = wav_file.getnframes()
            
        print(f"✅ WAV file verified: {channels} channels, {sample_width} bytes/sample, {framerate} Hz, {frames} frames")
        
        # Clean up
        os.unlink(audio_file)
        print(f"✅ Cleaned up test file")
        return True
        
    except Exception as e:
        print(f"❌ Audio file creation failed: {e}")
        return False

def test_dependencies():
    """Test if key dependencies are available"""
    print("\n=== Testing Dependencies ===")
    
    deps = {
        'numpy': np,
    }
    
    optional_deps = ['demucs', 'basic_pitch', 'music21']
    
    for name, module in deps.items():
        try:
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {name}: {version}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            return False
    
    for name in optional_deps:
        try:
            __import__(name)
            print(f"✅ {name}: available")
        except ImportError:
            print(f"⚠️  {name}: not available (expected if not installed)")
    
    return True

def test_file_structure():
    """Test the project file structure"""
    print("\n=== Testing Project Structure ===")
    
    required_dirs = ['backend', 'frontend', 'uploads', 'processed']
    required_files = ['backend/server.py', 'frontend/src/App.js', 'backend_test.py']
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            return False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            return False
    
    return True

def run_simple_tests():
    """Run all simple tests"""
    print("🎵 Starting Simple Functionality Tests 🎵")
    print("=" * 50)
    
    results = {
        'file_structure': False,
        'dependencies': False,
        'audio_creation': False,
    }
    
    # Test file structure
    results['file_structure'] = test_file_structure()
    
    # Test dependencies
    results['dependencies'] = test_dependencies()
    
    # Test audio file creation
    results['audio_creation'] = test_audio_file_creation()
    
    # Print results
    print("\n" + "=" * 50)
    print("🎵 SIMPLE TEST RESULTS 🎵")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All basic functionality tests passed!")
    else:
        print("⚠️  Some tests failed.")
    
    return results

if __name__ == "__main__":
    run_simple_tests()
