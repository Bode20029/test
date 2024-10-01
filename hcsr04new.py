import Jetson.GPIO as GPIO
import time
import logging
import statistics
import math

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
TRIG_PIN = 12  # Physical Pin 12
ECHO_PIN = 16  # Physical Pin 16
MIN_DISTANCE = 2  # cm
MAX_DISTANCE = 400  # cm
TIMEOUT = 0.1  # seconds
MEASUREMENT_INTERVAL = 1  # seconds
SPEED_OF_SOUND = 343  # m/s at 20?C
MEASUREMENTS_PER_SAMPLE = 5
TEMPERATURE_SENSOR_PIN = 18  # Assuming we have a temperature sensor connected

def setup_gpio():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    GPIO.setup(TEMPERATURE_SENSOR_PIN, GPIO.IN)  # Set up temperature sensor pin

def get_temperature():
    # This is a placeholder. Replace with actual code to read from your temperature sensor
    return 20  # Assuming 20?C if we can't read the temperature

def calculate_speed_of_sound(temperature):
    return 331.3 + 0.606 * temperature

def get_single_distance(speed_of_sound):
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.00001)
    
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)
    
    pulse_start = pulse_end = time.time()
    timeout = pulse_start + TIMEOUT
    
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None
    
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None
    
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * speed_of_sound * 100) / 2  # Convert to cm
    
    if distance < MIN_DISTANCE or distance > MAX_DISTANCE:
        return None
    
    return distance

def get_filtered_distance():
    temperature = get_temperature()
    speed_of_sound = calculate_speed_of_sound(temperature)
    
    measurements = []
    for _ in range(MEASUREMENTS_PER_SAMPLE):
        dist = get_single_distance(speed_of_sound)
        if dist is not None:
            measurements.append(dist)
        time.sleep(0.01)  # Short delay between measurements
    
    if len(measurements) < 3:
        logging.warning("Not enough valid measurements")
        return None
    
    # Use median to filter out outliers
    median_distance = statistics.median(measurements)
    
    # Calculate standard deviation
    std_dev = statistics.stdev(measurements)
    
    # Filter measurements within 2 standard deviations of the median
    filtered_measurements = [d for d in measurements if abs(d - median_distance) <= 2 * std_dev]
    
    if not filtered_measurements:
        logging.warning("All measurements filtered out")
        return None
    
    # Calculate the average of the filtered measurements
    average_distance = sum(filtered_measurements) / len(filtered_measurements)
    
    return round(average_distance, 2)

def main():
    setup_gpio()
    try:
        while True:
            dist = get_filtered_distance()
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