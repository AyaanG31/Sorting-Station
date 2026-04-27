import cv2
import numpy as np
from picamera2 import Picamera2

# 1. Setup Camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={'format': 'RGB888', 'size': (640, 640)})
picam2.configure(config)
picam2.start()

# Variables to store clicks
click_x, click_y = 0, 0

def mouse_callback(event, x, y, flags, param):
    global click_x, click_y
    if event == cv2.EVENT_LBUTTONDOWN:
        click_x, click_y = x, y
        print(f"Pixel Coordinates -> X: {x}, Y: {y}")

# Create window and bind the mouse function
cv2.namedWindow("Calibration Mode")
cv2.setMouseCallback("Calibration Mode", mouse_callback)

try:
    print("--- Calibration Mode ---")
    print("1. Click the center of your robot base to find OFFSET_X and OFFSET_Y.")
    print("2. Click two points exactly 10cm apart to calculate PIXELS_PER_CM.")
    print("Press 'q' to quit.")

    while True:
        frame = picam2.capture_array()
        
        # Draw a crosshair at the last clicked point
        cv2.drawMarker(frame, (click_x, click_y), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(frame, f"X:{click_x} Y:{click_y}", (click_x + 10, click_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("Calibration Mode", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()