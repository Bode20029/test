import time
import cv2
import datetime
import logging
import requests
import os

# Import from existing files
from hc_sr04p_distance2 import HCSR04P
from Updated_PZEM_Sensor_Reader_Script import connect_to_sensor, read_sensor_data

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MIN_DISTANCE = 20  # cm
DISTANCE_DETECTION_TIME = 3  # seconds
FACE_DETECTION_TIME = 5  # seconds
PZEM_MONITORING_TIME = 120  # seconds
LINE_TOKEN = "J0oQ74OftbCNdiPCCfV4gs75aqtz4aAL8NiGfHERvZ4"

# OpenCV setup
def find_haar_cascade(filename):
    opencv_home = cv2.__file__
    subfolder = os.path.dirname(os.path.dirname(opencv_home))
    haar_file = os.path.join(subfolder, 'data', 'haarcascades', filename)
    if not os.path.isfile(haar_file):
        raise FileNotFoundError(f"{filename} not found. Please check OpenCV installation.")
    return haar_file

face_cascade = cv2.CascadeClassifier(find_haar_cascade('haarcascade_frontalface_default.xml'))
body_cascade = cv2.CascadeClassifier(find_haar_cascade('haarcascade_fullbody.xml'))

def send_line_notification(message):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {LINE_TOKEN}'}
    payload = {'message': message}
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        logger.info("LINE notification sent successfully")
    else:
        logger.error(f"Failed to send LINE notification: {response.text}")

def main():
    # Initialize sensors
    distance_sensor = HCSR04P(trigger_pin=23, echo_pin=24)
    pzem_master = connect_to_sensor()
    cap = cv2.VideoCapture(0)

    distance_detection_start = None
    face_detection_start = None
    pzem_monitoring_start = None

    try:
        while True:
            # Check distance
            distance = distance_sensor.filtered_distance()
            if distance is not None and distance < MIN_DISTANCE:
                if distance_detection_start is None:
                    distance_detection_start = time.time()
                elif time.time() - distance_detection_start >= DISTANCE_DETECTION_TIME:
                    logger.info(f"Object detected at {distance} cm for {DISTANCE_DETECTION_TIME} seconds")
                    
                    # Start face/body detection
                    face_detection_start = time.time()
                    while time.time() - face_detection_start < FACE_DETECTION_TIME:
                        _, frame = cap.read()
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                        bodies = body_cascade.detectMultiScale(gray, 1.3, 5)
                        
                        if len(faces) + len(bodies) > 0:
                            logger.info("Human detected")
                            pzem_monitoring_start = time.time()
                            
                            # Monitor PZEM for 2 minutes
                            while time.time() - pzem_monitoring_start < PZEM_MONITORING_TIME:
                                pzem_data = read_sensor_data(pzem_master)
                                logger.info(f"PZEM data: {pzem_data}")
                                time.sleep(1)
                            
                            send_line_notification("A Human not charging 1 ea")
                            break
                        
                        cv2.imshow("Camera", frame)
                        if cv2.waitKey(1) == ord('q'):
                            return
                    
                    # Reset detection
                    distance_detection_start = None
                    face_detection_start = None
                    pzem_monitoring_start = None
            else:
                distance_detection_start = None
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if pzem_master:
            pzem_master.close()

if __name__ == "__main__":
    main()