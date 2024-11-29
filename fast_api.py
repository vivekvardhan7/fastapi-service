import cv2
from dotenv import load_dotenv
import mediapipe as mp
import requests
import tempfile
import os
from azure.storage.blob import BlobServiceClient, ContentSettings
load_dotenv()

# Initialize MediaPipe for face and landmark detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Azure Blob Storage Configuration
AZURE_CONNECTION_STRING = os.getenv("proxy_connect_str")
AZURE_CONTAINER_NAME = os.getenv("proxy_container_name")

# Azure Blob Storage Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
blob_container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

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

def upload_to_azure(file_path, blob_name):
    """Upload a file to Azure Blob Storage and return the file URL."""
    try:
        with open(file_path, "rb") as data:
            content_settings = ContentSettings(content_type="image/jpeg")
            blob_client = blob_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
        return blob_client.url
    except Exception as e:
        print(f"Failed to upload to Azure: {e}")
        return None

def save_screenshot(frame, timestamp, video_name):
    """Save the current frame as a screenshot and upload it to Azure."""
    screenshot_name = f"{video_name}_screenshot_{timestamp}.jpg"
    local_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
    cv2.imwrite(local_path, frame)  # Save frame locally
    
    # Upload to Azure
    azure_url = upload_to_azure(local_path, screenshot_name)
    
    # Clean up local file
    os.remove(local_path)
    
    return azure_url

def analyze_video_stream(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 30  # Fallback if FPS is not provided
    results_list = []  # To store the results as per the desired format

    last_processed_second = -1  # Track the last second processed to avoid duplicates
    video_name = os.path.basename(video_path).split('.')[0]  # Extract video name for blob naming

    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            timestamp_in_seconds = int(frame_count / fps)  # Get timestamp in seconds

            # Process only once per second
            if timestamp_in_seconds > last_processed_second:
                last_processed_second = timestamp_in_seconds


                # Convert frame to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb_frame)

                # Default values
                head_position = "unknown"
                multiple_face_detection = False

                if results.detections:
                    face_count = len(results.detections)
                    if face_count > 1:
                        multiple_face_detection = True
                    
                    for detection in results.detections:
                        # Improved head orientation analysis
                        bbox = detection.location_data.relative_bounding_box
                        if bbox.xmin < 0.3:
                            head_position = "left"
                        elif bbox.xmin > 0.7:
                            head_position = "right"
                        else:
                            head_position = "forward"
                else:
                    head_position = "away"  # No face detected
                if head_position != "forward":
                        # Save the current frame and upload to Azure
                        azure_url = save_screenshot(frame, timestamp_in_seconds, video_name)
                        results_list.append({
                    "time": timestamp_in_seconds,
                    "head_position": head_position,
                    "multiple_face_detection": multiple_face_detection,
                    "screenshot_url": azure_url      })
                        
                else:
                # Append results for the current timestamp
                    results_list.append({
                    "time": timestamp_in_seconds,
                    "head_position": head_position,
                    "multiple_face_detection": multiple_face_detection
                })

    cap.release()
    return results_list


def analyze_video_endpoint(video_url):
    if not video_url:
        return {"error": "No video URL provided"}

    # Download the video temporarily if needed
    video_path = download_video(video_url)
    if not video_path:
        return {"error": "Failed to download video from the URL provided"}

    # Perform analysis on the video
    result = analyze_video_stream(video_path)

    # Clean up the downloaded video file
    os.remove(video_path)

    return {"analysis_result": result}


# # Example usage
# video_url = "https://jobfairreaidy.blob.core.windows.net/recordings/6734e016df0d8f51c5d50c38.mp4"
# result = analyze_video_endpoint(video_url)
# print(result)

# requirements
# opencv-python
# mediapipe 
# requests
# azure_functions
# azure_storage_blob 
# python_dotenv
