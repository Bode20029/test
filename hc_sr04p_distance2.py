import RPi.GPIO as GPIO
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
MIN_DISTANCE = 2  # cm
MAX_DISTANCE = 400  # cm
TIMEOUT = 1.0  # seconds
MEASUREMENT_INTERVAL = 1  # seconds

class HCSR04P:
    def __init__(self, trigger_pin, echo_pin, mode=GPIO.BCM):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        
        if not GPIO.getmode():
            GPIO.setmode(mode)
        
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        self.last_valid_distance = None

    def get_distance(self):
        GPIO.output(self.trigger_pin, GPIO.LOW)
        time.sleep(0.1)
        
        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)
        
        pulse_start = pulse_end = time.time()
        timeout = pulse_start + TIMEOUT
        
        while GPIO.input(self.echo_pin) == GPIO.LOW:
            pulse_start = time.time()
            if pulse_start > timeout:
                logging.warning("Echo pulse start timeout")
                return None
        
        while GPIO.input(self.echo_pin) == GPIO.HIGH:
            pulse_end = time.time()
            if pulse_end > timeout:
                logging.warning("Echo pulse end timeout")
                return None
        
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        
        if distance < MIN_DISTANCE or distance > MAX_DISTANCE:
            logging.warning(f"Distance out of range: {distance} cm")
            return None
        
        return round(distance, 2)

    def filtered_distance(self):
        for _ in range(3):
            dist = self.get_distance()
            if dist is not None:
                if self.last_valid_distance is None or abs(dist - self.last_valid_distance) < 50:
                    self.last_valid_distance = dist
                    return dist
        logging.warning("Failed to get a valid distance after 3 attempts")
        return None

def main():
    # Example usage
    sensor = HCSR04P(trigger_pin=23, echo_pin=24)  # Using BCM pin numbering
    
    try:
        while True:
            dist = sensor.filtered_distance()
            if dist is None:
                logging.error("Measurement error or out of range")
            else:
                logging.info(f"Measured Distance = {dist} cm")
            time.sleep(MEASUREMENT_INTERVAL)
    except KeyboardInterrupt:
        logging.info("Measurement stopped by user")
    finally:
        GPIO.cleanup()
        logging.info("GPIO cleanup completed")

if __name__ == "__main__":
    main()