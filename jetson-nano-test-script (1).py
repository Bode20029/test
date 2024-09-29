import cv2
import time
from ultralytics import YOLO
import numpy as np
from hc_sr04p_distance import filtered_distance

# Load YOLOv8 model
model = YOLO('path/to/your/yolov8_model.pt')

# Initialize video capture
cap = cv2.VideoCapture(0)  # Use 0 for default camera, adjust if necessary

# Constants
DISTANCE_THRESHOLD = 60  # cm
STABLE_DETECTION_TIME = 5  # seconds
CONFIDENCE_THRESHOLD = 0.5

# Variables to track detection stability
last_detection = None
stable_detection_start = None

def is_ev(detections):
    # Adjust this function based on your model's classes
    # Assuming 'EV' or 'electric vehicle' is one of the classes
    for det in detections:
        if det.cls == 'EV' or det.cls == 'electric vehicle':
            return True
    return False

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Run YOLOv8 inference on the frame
        results = model(frame)

        # Process results
        current_detection = None
        for r in results:
            if r.boxes:
                # Assuming we're interested in the most confident detection
                box = r.boxes[0]
                if box.conf > CONFIDENCE_THRESHOLD:
                    current_detection = (box.cls.item(), box.conf.item(), box.xywh[0].tolist())

        # Check for stable detection
        if current_detection:
            if current_detection == last_detection:
                if stable_detection_start is None:
                    stable_detection_start = time.time()
                elif time.time() - stable_detection_start >= STABLE_DETECTION_TIME:
                    # Stable detection achieved, now check distance
                    distance = filtered_distance()
                    if distance is not None and distance < DISTANCE_THRESHOLD:
                        if is_ev(r.boxes):
                            print("yes")
                        else:
                            print("no")
                        # Reset after printing result
                        stable_detection_start = None
            else:
                stable_detection_start = None
        else:
            stable_detection_start = None

        last_detection = current_detection

        # Display the frame with bounding boxes
        for r in results:
            annotated_frame = r.plot()
            cv2.imshow("YOLOv8 Inference", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.1)  # Small delay to reduce CPU usage

except KeyboardInterrupt:
    print("Test interrupted by user")
finally:
    cap.release()
    cv2.destroyAllWindows()
