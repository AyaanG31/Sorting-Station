import cv2
import threading
import time
from ultralytics import YOLO
from picamera2 import Picamera2

# 1. Load Model
model = YOLO("yolov8n_ncnn_model", task='detect')

# 2. Camera Setup
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={'format': 'RGB888', 'size': (640, 640)})
picam2.configure(config)
picam2.start()

frame_lock = threading.Lock()
latest_frame = None
running = True

def capture_thread():
    global latest_frame, running
    while running:
        img = picam2.capture_array()
        with frame_lock:
            latest_frame = img

t = threading.Thread(target=capture_thread, daemon=True)
t.start()

# Variables for FPS
prev_time = time.time()

try:
    while True:
        if latest_frame is None: continue

        with frame_lock:
            # Copy to prevent the capture thread from updating the frame while we draw
            frame = latest_frame.copy()
        
        # 3. Predict
        results = model.predict(
            source=frame, 
            conf=0.1,      
            iou=0.45,      
            save=False, 
            verbose=False, 
            stream=True
        )

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Bounding Box
                color = (0, 255, 0) 
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Label
                text = f"ID:{cls_id} {label} {conf:.2f}"
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # --- FPS Calculation ---
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time

        # Draw FPS on frame
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow("Multi-Object Debugger", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    running = False
    t.join()
    picam2.stop()
    cv2.destroyAllWindows()