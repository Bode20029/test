import RPi.GPIO as GPIO
from hc_sr04p_distance import HCSR04P
import time
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DISTANCE_THRESHOLD = 150  # cm
MEASUREMENT_INTERVAL = 1  # seconds
NOTIFICATION_COOLDOWN = 60  # seconds

# Line Notify Token
LINE_NOTIFY_TOKEN = 'YOUR_LINE_NOTIFY_TOKEN'  # Replace with your actual token

def send_line_notify(message):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'}
    data = {'message': message}
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            logging.info("Line Notify sent successfully")
        else:
            logging.error(f"Failed to send Line Notify. Status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Error sending Line Notify: {e}")

def main():
    # Set up GPIO mode
    GPIO.setmode(GPIO.BCM)  # or GPIO.BOARD if you prefer

    # Initialize the sensor
    # If using BCM mode:
    sensor = HCSR04P(trigger_pin=23, echo_pin=24, mode=GPIO.BCM)
    # If using BOARD mode:
    # sensor = HCSR04P(trigger_pin=16, echo_pin=18, mode=GPIO.BOARD)

    last_notification_time = 0

    logging.info("Distance measurement and Line Notify script is running...")
    logging.info(f"Detection threshold: {DISTANCE_THRESHOLD} cm")

    try:
        while True:
            distance = sensor.filtered_distance()
            
            if distance is not None:
                logging.info(f"Measured distance: {distance} cm")
                
                if distance < DISTANCE_THRESHOLD:
                    current_time = time.time()
                    if current_time - last_notification_time > NOTIFICATION_COOLDOWN:
                        message = f"Object detected within range! Distance: {distance} cm"
                        logging.info(message)
                        send_line_notify(message)
                        last_notification_time = current_time
            else:
                logging.warning("Failed to get distance measurement")

            time.sleep(MEASUREMENT_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Script stopped by user")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
    finally:
        GPIO.cleanup()
        logging.info("GPIO cleaned up")

if __name__ == "__main__":
    main()