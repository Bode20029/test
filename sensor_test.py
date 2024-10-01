import time
from hc_sr04p_distance import filtered_distance, setup_gpio
import requests
import Jetson.GPIO as GPIO

# Constants
DISTANCE_THRESHOLD = 60  # cm
STABLE_DETECTION_TIME = 5  # seconds
MEASUREMENT_INTERVAL = 2.5  # seconds

# Line Notify Token
LINE_NOTIFY_TOKEN = 'J0oQ74OftbCNdiPCCfV4gs75aqtz4aAL8NiGfHERvZ4'

# Variables to track detection stability
last_stable_distance = None
stable_detection_start = None

def send_line_notify(message):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'}
    data = {'message': message}
    response = requests.post(url, headers=headers, data=data)
    return response.status_code == 200

try:
    # Ensure GPIO is set up
    setup_gpio()
    
    print("Starting distance-based detection...")
    while True:
        distance = filtered_distance()
        
        if distance is not None:
            print(f"Measured distance: {distance} cm")
            
            if distance < DISTANCE_THRESHOLD:
                if last_stable_distance is None or abs(distance - last_stable_distance) < 5:
                    if stable_detection_start is None:
                        stable_detection_start = time.time()
                    elif time.time() - stable_detection_start >= STABLE_DETECTION_TIME:
                        print(f"Stable detection within {DISTANCE_THRESHOLD} cm for {STABLE_DETECTION_TIME} seconds")
                        send_line_notify(f"Object detected within {DISTANCE_THRESHOLD} cm range.")
                        stable_detection_start = None  # Reset after sending notification
                else:
                    stable_detection_start = None
            else:
                stable_detection_start = None
            
            last_stable_distance = distance
        else:
            print("Failed to get a valid distance measurement")
            stable_detection_start = None
        
        time.sleep(MEASUREMENT_INTERVAL)

except KeyboardInterrupt:
    print("Test interrupted by user")
except Exception as e:
    print(f"An error occurred: {e}")
    send_line_notify(f"Error in distance detection system: {e}")
finally:
    GPIO.cleanup()
    print("GPIO cleanup completed")
    print("Exiting the program")