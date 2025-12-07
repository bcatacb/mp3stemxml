#!/usr/bin/env python3
"""
Backend Test Suite for Audio to MIDI Converter
Tests the complete workflow: upload -> processing -> download
"""

import requests
import time
import os
import tempfile
import zipfile
import numpy as np
import wave
from pathlib import Path
import json

# Get backend URL from frontend .env file
def get_backend_url():
    env_path = Path("frontend/.env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    return "https://granular-stems.preview.emergentagent.com"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"Testing backend at: {API_URL}")

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

def test_api_health():
    """Test the basic API health endpoint"""
    print("\n=== Testing API Health Endpoint ===")
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print("❌ API health check failed")
            return False
    except Exception as e:
        print(f"❌ API health check failed with error: {e}")
        return False

def test_file_upload(audio_file_path):
    """Test file upload endpoint"""
    print("\n=== Testing File Upload Endpoint ===")
    try:
        with open(audio_file_path, 'rb') as f:
            files = {'file': ('test_audio.wav', f, 'audio/wav')}
            response = requests.post(f"{API_URL}/upload", files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            job_id = response.json().get('job_id')
            print(f"✅ File upload successful, job_id: {job_id}")
            return job_id
        else:
            print("❌ File upload failed")
            return None
    except Exception as e:
        print(f"❌ File upload failed with error: {e}")
        return None

def test_job_status(job_id, max_wait_time=300):
    """Test job status tracking and wait for completion"""
    print(f"\n=== Testing Job Status Tracking (Job ID: {job_id}) ===")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{API_URL}/status/{job_id}", timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"Status: {status_data['status']}")
                print(f"Progress: {status_data['progress']}%")
                print(f"Message: {status_data['message']}")
                
                if status_data['status'] == 'completed':
                    print("✅ Job completed successfully")
                    return True
                elif status_data['status'] == 'failed':
                    print("❌ Job failed")
                    return False
                else:
                    print("⏳ Job still processing, waiting 10 seconds...")
                    time.sleep(10)
            else:
                print(f"❌ Status check failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Status check failed with error: {e}")
            return False
    
    print("❌ Job did not complete within the maximum wait time")
    return False

def test_file_download(job_id):
    """Test file download endpoint"""
    print(f"\n=== Testing File Download (Job ID: {job_id}) ===")
    try:
        response = requests.get(f"{API_URL}/download/{job_id}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save the downloaded file
            download_path = f"/tmp/test_download_{job_id}.zip"
            with open(download_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ File downloaded successfully: {download_path}")
            print(f"File size: {len(response.content)} bytes")
            
            # Verify ZIP contents
            return verify_zip_contents(download_path)
        else:
            print(f"❌ File download failed with status code: {response.status_code}")
            try:
                print(f"Error response: {response.json()}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ File download failed with error: {e}")
        return False

def verify_zip_contents(zip_path):
    """Verify the downloaded ZIP contains expected folders and files"""
    print(f"\n=== Verifying ZIP Contents ===")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            print(f"Files in ZIP: {len(file_list)}")
            
            # Check for required folders
            stems_files = [f for f in file_list if f.startswith('stems/')]
            midi_files = [f for f in file_list if f.startswith('midi/')]
            musicxml_files = [f for f in file_list if f.startswith('musicxml/')]
            
            print(f"Stems files: {len(stems_files)}")
            for f in stems_files:
                print(f"  - {f}")
            
            print(f"MIDI files: {len(midi_files)}")
            for f in midi_files:
                print(f"  - {f}")
            
            print(f"MusicXML files: {len(musicxml_files)}")
            for f in musicxml_files:
                print(f"  - {f}")
            
            # Verify we have files in all expected folders
            success = True
            if len(stems_files) == 0:
                print("❌ No stems files found")
                success = False
            else:
                print("✅ Stems files found")
            
            if len(midi_files) == 0:
                print("❌ No MIDI files found")
                success = False
            else:
                print("✅ MIDI files found")
            
            if len(musicxml_files) == 0:
                print("⚠️  No MusicXML files found (may be expected if conversion failed)")
                # Don't fail the test for missing MusicXML as it's noted in the code that conversion can fail
            else:
                print("✅ MusicXML files found")
            
            return success
            
    except Exception as e:
        print(f"❌ ZIP verification failed with error: {e}")
        return False

def run_complete_test():
    """Run the complete test suite"""
    print("🎵 Starting Audio to MIDI Converter Backend Test Suite 🎵")
    print("=" * 60)
    
    # Test results tracking
    results = {
        'api_health': False,
        'file_upload': False,
        'job_status': False,
        'file_download': False,
        'zip_verification': False
    }
    
    # Step 1: Test API health
    results['api_health'] = test_api_health()
    if not results['api_health']:
        print("\n❌ API health check failed. Cannot proceed with other tests.")
        return results
    
    # Step 2: Create test audio file
    print("\n=== Creating Test Audio File ===")
    audio_file = create_test_audio_file(duration=3)  # Short 3-second file
    print(f"Test audio file created: {audio_file}")
    
    try:
        # Step 3: Test file upload
        job_id = test_file_upload(audio_file)
        if job_id:
            results['file_upload'] = True
            
            # Step 4: Test job status tracking
            if test_job_status(job_id, max_wait_time=300):  # 5 minutes max
                results['job_status'] = True
                
                # Step 5: Test file download
                if test_file_download(job_id):
                    results['file_download'] = True
                    results['zip_verification'] = True  # Set by verify_zip_contents
    
    finally:
        # Clean up test audio file
        try:
            os.unlink(audio_file)
            print(f"Cleaned up test audio file: {audio_file}")
        except:
            pass
    
    # Print final results
    print("\n" + "=" * 60)
    print("🎵 TEST RESULTS SUMMARY 🎵")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The Audio to MIDI Converter backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the detailed output above.")
    
    return results

if __name__ == "__main__":
    run_complete_test()