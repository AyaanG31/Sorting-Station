import pigpio
import time

# --- GPIO SETUP ---
SERVO_BASE = 18
SERVO_SHOULDER = 23
SERVO_ELBOW = 24
# DRV8833 Pins
GRIP_IN1 = 13
GRIP_IN2 = 12

# Speed setting (0.02 is steady, 0.05 is very slow)
MOVE_SPEED = 0.02

pi = pigpio.pi()
if not pi.connected:
    print("Could not connect to pigpiod. Run 'sudo pigpiod' first.")
    exit()

# Global tracking for smooth movement
curr_angles = {"base": 90, "shoulder": 80, "elbow": 180}

def smooth_move(pin, target_angle, motor_name):
    """Gradually moves servo to target and updates global state."""
    global curr_angles
    current = curr_angles[motor_name]
    step = 1 if target_angle > current else -1
    
    for angle in range(int(current), int(target_angle) + step, step):
        # Safety clamp
        angle = max(0, min(180, angle))
        pulsewidth = 500 + (angle / 180.0) * 2000
        pi.set_servo_pulsewidth(pin, pulsewidth)
        time.sleep(MOVE_SPEED)
    
    curr_angles[motor_name] = target_angle

def control_gripper(action, speed=200):
    """DRV8833 Logic: IN1=PWM/IN2=0 for one way, vice versa for other."""
    if action == "open":
        pi.write(GRIP_IN1, 0)
        pi.set_PWM_dutycycle(GRIP_IN2, speed)
    elif action == "close":
        pi.set_PWM_dutycycle(GRIP_IN1, speed)
        pi.write(GRIP_IN2, 0)
    else: # stop
        pi.write(GRIP_IN1, 0)
        pi.write(GRIP_IN2, 0)

try:
    # Initialize to neutral 90 degrees
    for motor, pin in [("base", SERVO_BASE), ("shoulder", SERVO_SHOULDER), ("elbow", SERVO_ELBOW)]:
        pi.set_servo_pulsewidth(pin, 500 + (90/180.0)*2000)
    
    print("--- Smooth Servo & Gripper Calibrator ---")
    print("Commands:")
    print("  base [0-180]      (e.g. base 120)")
    print("  shoulder [0-180]")
    print("  elbow [0-180]")
    print("  open [0-255]      (e.g. open 150)")
    print("  close [0-255]")
    print("  stop")
    print("  q                 (to quit)")

    while True:
        print(f"\nCurrent: B:{curr_angles['base']} S:{curr_angles['shoulder']} E:{curr_angles['elbow']}")
        inp = input(">> ").lower().split()
        
        if not inp: continue
        cmd = inp[0]
        if cmd == 'q': break
        
        try:
            val = int(inp[1]) if len(inp) > 1 else 200
            
            if cmd == "base":
                smooth_move(SERVO_BASE, val, "base")
            elif cmd == "shoulder":
                smooth_move(SERVO_SHOULDER, val, "shoulder")
            elif cmd == "elbow":
                smooth_move(SERVO_ELBOW, val, "elbow")
            elif cmd == "open":
                print(f"Opening at speed {val}...")
                control_gripper("open", val)
            elif cmd == "close":
                print(f"Closing at speed {val}...")
                control_gripper("close", val)
            elif cmd == "stop":
                control_gripper("stop")
            else:
                print("Invalid motor. Use base, shoulder, elbow, open, close, or stop.")
        
        except (ValueError, IndexError):
            print("Usage: [motor] [value]")

finally:
    # Cleanup
    control_gripper("stop")
    pi.set_servo_pulsewidth(SERVO_BASE, 0)
    pi.set_servo_pulsewidth(SERVO_SHOULDER, 0)
    pi.set_servo_pulsewidth(SERVO_ELBOW, 0)
    pi.stop()
    print("Calibration finished. Servos released.")