import cv2
import threading
import time
import pigpio
from ultralytics import YOLO
from picamera2 import Picamera2

# --- 1. SETTINGS & CALIBRATION ---
CONF_THRESHOLD = 0.1  
REQUIRED_FRAMES = 2    
CLASS_IDS = [0, 1] 
MOVE_SPEED = 0.015  # Higher = Slower (Time in seconds between 1-degree steps)

# Regions
ROI_A = (340, 245, 448, 369)   
ROI_B = (500, 410, 628, 560)  

# Positions (Angles: Base, Shoulder, Elbow)
POS_HOME      = (0, 80, 150)
POS_DROP_ZONE = (68, 50, 180)
POS_COMPLETE  = (0, 80, 98)
# Region A
POS_A_HOVER   = (114, 88, 180)
POS_A_PICK    = (114, 88, 66)
# Region B
POS_B_HOVER   = (180, 83, 150)
POS_B_PICK    = (180, 83, 72)

# Global variables to track current physical position of servos
curr_b, curr_s, curr_e = POS_HOME

# Hardware Pins
SERVO_BASE, SERVO_SHOULDER, SERVO_ELBOW = 18, 23, 24
GRIP_IN1, GRIP_IN2 = 13, 12 

pi = pigpio.pi()
if not pi.connected:
    print("Error: pigpiod not running.")
    exit()

# --- 2. HELPERS ---
def smooth_move(pin, target_angle, current_angle, speed):
    """Increments servo angle by 1 degree to create slow, smooth movement."""
    step = 1 if target_angle > current_angle else -1
    
    # Range is from current to target inclusive
    for angle in range(int(current_angle), int(target_angle) + step, step):
        # Prevent going out of physical bounds
        angle = max(0, min(180, angle))
        pulsewidth = 500 + (angle / 180.0) * 2000
        pi.set_servo_pulsewidth(pin, pulsewidth)
        time.sleep(speed) 
    
    return target_angle

def set_arm(angles):
    """Moves servos sequentially with smooth stepping and 2s delays."""
    global curr_b, curr_s, curr_e
    target_b, target_s, target_e = angles
    
    # 1. Move Base
    curr_b = smooth_move(SERVO_BASE, target_b, curr_b, MOVE_SPEED)
    time.sleep(2)
    
    # 2. Move Shoulder
    curr_s = smooth_move(SERVO_SHOULDER, target_s, curr_s, MOVE_SPEED)
    time.sleep(2)
    
    # 3. Move Elbow
    curr_e = smooth_move(SERVO_ELBOW, target_e, curr_e, MOVE_SPEED)
    time.sleep(2)

def control_gripper(action, speed=150):
    """DRV8833 Logic."""
    if action == "close":
        pi.set_PWM_dutycycle(GRIP_IN1, speed)
        pi.write(GRIP_IN2, 0)
    elif action == "open":
        pi.write(GRIP_IN1, 0)
        pi.set_PWM_dutycycle(GRIP_IN2, speed)
    else: # stop
        pi.write(GRIP_IN1, 0)
        pi.write(GRIP_IN2, 0)

# --- 3. VISION ---
model = YOLO("yolov8n_ncnn_model", task='detect') 
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
        with frame_lock: latest_frame = img

threading.Thread(target=capture_thread, daemon=True).start()

# --- 4. MAIN LOOP ---
count_a, count_b = 0, 0

try:
    print("System Online. Starting slow-move scanner...")
    # Setup initial position immediately without smooth_move to calibrate start
    pi.set_servo_pulsewidth(SERVO_BASE, 500 + (POS_HOME[0] / 180.0) * 2000)
    pi.set_servo_pulsewidth(SERVO_SHOULDER, 500 + (POS_HOME[1] / 180.0) * 2000)
    pi.set_servo_pulsewidth(SERVO_ELBOW, 500 + (POS_HOME[2] / 180.0) * 2000)
    time.sleep(2)

    while True:
        if latest_frame is None: continue
        with frame_lock: frame = latest_frame.copy()
        
        cv2.rectangle(frame, (ROI_A[0], ROI_A[1]), (ROI_A[2], ROI_A[3]), (255, 0, 0), 2)
        cv2.rectangle(frame, (ROI_B[0], ROI_B[1]), (ROI_B[2], ROI_B[3]), (0, 255, 255), 2)

        results = model.predict(source=frame, imgsz=320, conf=CONF_THRESHOLD, verbose=False, classes=CLASS_IDS)
        
        found_a, found_b = False, False

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                
                if ROI_A[0] <= cx <= ROI_A[2] and ROI_A[1] <= cy <= ROI_A[3]:
                    found_a = True
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                elif ROI_B[0] <= cx <= ROI_B[2] and ROI_B[1] <= cy <= ROI_B[3]:
                    found_b = True
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

        count_a = count_a + 1 if found_a else 0
        count_b = count_b + 1 if found_b else 0

        target_roi = None
        if count_a >= REQUIRED_FRAMES: target_roi = "A"
        elif count_b >= REQUIRED_FRAMES: target_roi = "B"

        if target_roi:
            print(f"STABLE TARGET IN ROI {target_roi}. Moving slowly...")
            h_pos = POS_A_HOVER if target_roi == "A" else POS_B_HOVER
            p_pos = POS_A_PICK if target_roi == "A" else POS_B_PICK
            
            set_arm(h_pos)
            control_gripper("open")
            time.sleep(3)
            control_gripper("stop")
            set_arm(p_pos)
            
            control_gripper("close", 200)
            time.sleep(3)
            
            set_arm(h_pos)
            if target_roi == "A":
                set_arm(POS_DROP_ZONE)
            else:
                set_arm(POS_COMPLETE)
            
            control_gripper("open", 200)
            time.sleep(3)
            control_gripper("close")
            time.sleep(5)
            control_gripper("stop")
            
            count_a, count_b = 0, 0
            set_arm(POS_HOME)

        cv2.imshow("Slow-Scan Robot", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

finally:
    running = False
    picam2.stop()
    control_gripper("stop")
    pi.stop()
    cv2.destroyAllWindows()