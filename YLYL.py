import threading 
import time 
import random 
import requests 
import cv2 
from selenium import webdriver 
from selenium.webdriver.common.by import By 
import win32api 

API_KEY = "YOUR_GOOGLE_CONSOLE_API_TOKEN"
SMILE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Function to fetch random funny shorts or related videos
def fetch_youtube_shorts(query="funny shorts", related_video_id=None):
    humor_phrases = [
        "funny shorts", "dumb humor", "goofy sounds", "random laughs", "silly noises", 
        "stupid jokes", "laughing like crazy", "ridiculous memes", "random funny stuff", "silly antics",
        "brain rot", "dark humor", "funny animals", "unexpected sounds", "funny fails", "youtube poop",
        "2024 memes", "awkward moments", "cringe comedy", "dad jokes", "slapstick humor", 
        "hilarious pranks", "comedy gold", "absurd humor", "weirdly funny", "funny fails compilation",
        "laugh till you drop", "unbelievable funny moments", "prank wars", "memes compilation", 
        "ridiculous challenges", "funny dance moves", "laughing out loud", "laughing till you cry"
    ]
    
    if related_video_id:
        # Fetch related videos if provided a related_video_id
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "video",
            "maxResults": 10,
            "videoDuration": "short",
            "key": API_KEY,
            "relevanceLanguage": "en",
            "relatedToVideoId": related_video_id
        }
    else:
        query = random.choice(humor_phrases)
        # Fetch random funny shorts if no related_video_id is provided
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "video",
            "maxResults": 10,
            "videoDuration": "short",
            "key": API_KEY,
            "relevanceLanguage": "en",
            "q": query
        }

    response = requests.get(search_url, params=params)
    
    if response.status_code == 200:
        videos = response.json().get("items", [])
        valid_videos = []

        for video in videos:
            video_id = video['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={API_KEY}"
            video_details_response = requests.get(video_details_url)
            
            if video_details_response.status_code == 200:
                video_details = video_details_response.json()
                duration = video_details["items"][0]["contentDetails"]["duration"]
                seconds = convert_duration_to_seconds(duration)
                
                # Check if the video duration is <= 60 seconds
                if seconds <= 60:
                    valid_videos.append(f"https://www.youtube.com/shorts/{video_id}")
        
        return valid_videos
    
    return []

def convert_duration_to_seconds(duration):
    duration = duration.replace('PT', '')
    minutes = 0
    seconds = 0

    if 'M' in duration:
        minutes = int(duration.split('M')[0])
        duration = duration.split('M')[1]
    
    if 'S' in duration:
        seconds = int(duration.split('S')[0])

    total_seconds = (minutes * 60) + seconds
    return total_seconds

# Function to detect smile and count
def detect_smile_and_count(stop_flag):
    cap = cv2.VideoCapture(0)
    smile_count = 0
    try:
        while True:
            if stop_flag[0]:  # Check if the video has ended and stop smile detection
                print("Smile detection stopped.")
                break

            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            for (x, y, w, h) in faces:
                roi_gray = gray[y:y + h, x:x + w]
                smiles = SMILE_CASCADE.detectMultiScale(roi_gray, scaleFactor=1.3, minNeighbors=50)
                smile_count += len(smiles)

            cv2.imshow("Smile Detection", frame)
            
            # Check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):  # Press Q to quit
                break
            elif key == 27:  # Esc to quit the whole application
                print("Exiting...")
                stop_flag[0] = True
                break
            elif key == 32:  # Space to skip the video
                print("Skipping video...")
                stop_flag[0] = True
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
    return smile_count

# Function to play the video
def play_video(driver, video_url, stop_flag):
    driver.get(video_url)
    time.sleep(3)
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys("f")

    while True:
        try:
            current_time = driver.execute_script("return document.querySelector('video').currentTime;")
            duration = driver.execute_script("return document.querySelector('video').duration;")

            if current_time >= duration - 1:  # Buffer time before the video ends
                print("Video ended.")
                stop_flag[0] = True  # Set flag to stop smile detection
                break

        except Exception as e:
            print(f"Error monitoring video progress: {e}")
            break

        time.sleep(1)

# Function to play adaptive youtube shorts
def play_adaptive_youtube_shorts():
    driver = webdriver.Chrome()
    stop_flag = [False]  # List to allow passing by reference
    last_video_id = None  # Variable to store the last played video's ID

    try:
        while True:
            # Fetch random or related videos based on the last video ID
            # I didn't use this function instead I end the video player if the user laughs. Leaving this option to be used if desired
            youtube_shorts = fetch_youtube_shorts(related_video_id=last_video_id) if last_video_id else fetch_youtube_shorts()
            
            if not youtube_shorts:
                time.sleep(10)
                continue

            video_url = random.choice(youtube_shorts)
            video_id = video_url.split("/")[-1]  # Extract video ID from the URL

            # Start the video and smile detection (with shared stop_flag)
            video_thread = threading.Thread(target=play_video, args=(driver, video_url, stop_flag))
            video_thread.start()

            # Perform smile detection while the video plays
            smile_count = detect_smile_and_count(stop_flag)

            # Wait for video to finish
            video_thread.join()

            print(f"Smile count: {smile_count}")

            # Determine next video based on smile count
            if smile_count >= 50:
                win32api.MessageBox(0, '😂😂😂 YOU LAUGHED AT THE VIDEO YOU LOSE! 😭😭😭', 'YOU LOSE!', 0x00001000)
                driver.quit()
                break
            else:
                print("Fetching another random video...")

            # Reset the stop flag for the next video
            stop_flag[0] = False

            # Small delay before loading the next video
            time.sleep(2)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        driver.quit()

if __name__ == "__main__":
    play_adaptive_youtube_shorts()
