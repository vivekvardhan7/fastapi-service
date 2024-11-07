from fastapi import FastAPI, Request
import cv2
import mediapipe as mp
import requests
from datetime import timedelta
import tempfile
import os

app = FastAPI()

# Initialize MediaPipe for face and landmark detection
mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

def download_video(url):
    """Download video to a temporary file and return the path."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        return temp_file.name
    else:
        return None

def analyze_video_stream(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 30  # Fallback if FPS is not provided
    cheating_detected = False
    head_movements = []  # To store movements with timestamps

    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            timestamp = str(timedelta(seconds=int(frame_count / fps)))  # Get timestamp in HH:MM:SS format

            # Convert frame to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            # Count faces
            if results.detections:
                face_count = len(results.detections)
                if face_count > 1:
                    cheating_detected = True
                    head_movements.append(f"{timestamp}: Cheating detected - multiple faces")

                for detection in results.detections:
                    # Head orientation analysis (simplified for example)
                    # Here we would ideally use landmarks to check if head is left, right, or forward
                    # Placeholder: Assume forward for simplicity, modify with proper head detection logic
                    
                    head_position = "forward"  # Replace this with real orientation logic
                    head_movements.append(f"{timestamp}: Head position {head_position}")
            else:
                # If no face is detected, we could log as "away" if needed
                head_movements.append(f"{timestamp}: No face detected (away)")

    cap.release()
    
    # Prepare text output
    output_text = "Video Analysis Report:\n"
    output_text += "\n".join(head_movements)
    if cheating_detected:
        output_text += "\n\nNote: Cheating detected (multiple faces at some points in the video)."
    
    return output_text

@app.post("/analyze/")
async def analyze_video_endpoint(request: Request):
    data = await request.json()
    video_url = data.get("video_url")
    if not video_url:
        return {"error": "No video URL provided"}

    # Download the video temporarily if needed
    video_path = download_video(video_url)
    if not video_path:
        return {"error": "Failed to download video from the URL provided"}

    # Perform analysis on the video
    result_text = analyze_video_stream(video_path)

    # Clean up the downloaded video file
    os.remove(video_path)

    return {"text_result": result_text}

# Run the API with: uvicorn fast_api:app --reload
# Run the API with: uvicorn fast_api:app --reload
#FastAPI - for creating the API endpoints-pip install fastapi
#Uvicorn - ASGI server to serve FastAPI applications-pip install uvicorn
#OpenCV - for video handling and frame processing-pip install opencv-python
#MediaPipe - for face detection and landmark analysis-pip install mediapipe
#Requests - to download the video file from a URL-pip install requests
#post this in postman ---> http://127.0.0.1:8000/analyze/
