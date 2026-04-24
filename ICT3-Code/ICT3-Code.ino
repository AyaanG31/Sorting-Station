// --- TUNING PARAMETERS ---
unsigned long travel_time = 4000; 
unsigned long sticker_duration = 1500; 
unsigned long metal_reset_timer = 0;
unsigned long good_part_expiry = 0;
unsigned long rotary_open_ms = 1000; // Time (ms) solenoid O2 stays open
unsigned long delay_before_open_ms = 1000; // 2 seconds delay
bool inspection_complete = false;

int assem = 0;
int is_metal = 0; 
int onstate = 0;
int last_start_state = LOW; 
int ring_slide_time = 400;
int lastS2 = 0; 
int r2_busy = 0; 
int first_ring = 0;
unsigned long r2_timer = 0;

int last_feeder = 0; 

unsigned long refill_cooldown = 0;

// Input Pins (Sensors: LOW = Part Detected)
int s0 = 22; int s1 = 23; int s2 = 26; int s3 = 27;
int s4 = 30; int s5 = 31; int s6 = 34; int s7 = 35;
int s8 = 38; int s9 = 39; int s10 = 42;

// Output Pins (Active-Low Relays: LOW = ON, HIGH = OFF)
int o0 = 3; // Chain Conveyor OP0
int o1 = 4; // Sort Solenoid OP1
int o2 = 5; // Rotary Solenoid OP2
int o3 = 6; // Reject Solenoid Op3
int o4 = 7; // Belt Conveyor OP4

void setup() {
  Serial.begin(9600);
  
  pinMode(s0, INPUT); pinMode(s1, INPUT); pinMode(s2, INPUT); pinMode(s3, INPUT);
  pinMode(s4, INPUT); pinMode(s5, INPUT); pinMode(s6, INPUT); pinMode(s7, INPUT);
  pinMode(s8, INPUT); pinMode(s9, INPUT); pinMode(s10, INPUT);
  
  pinMode(o0, OUTPUT); pinMode(o1, OUTPUT); pinMode(o2, OUTPUT); 
  pinMode(o3, OUTPUT); pinMode(o4, OUTPUT);

  // STARTUP: All outputs HIGH (OFF for Active-Low)
  digitalWrite(o0, HIGH); digitalWrite(o1, HIGH); digitalWrite(o2, HIGH);
  digitalWrite(o3, HIGH); digitalWrite(o4, HIGH);

  Serial.println("System Initialized. Logic set to Active-Low.");
}

void loop() {
  unsigned long current_time = millis(); 
  
  // --- START / STOP LATCH ---
  int current_start = digitalRead(s6);
  if (current_start == HIGH && last_start_state == LOW) { 
    onstate = 1; 
    Serial.println(">> START");
  }
  last_start_state = current_start; 
  if (digitalRead(s7) == HIGH) { onstate = 0; }

  // --- RUNNING STATE ---
  if (onstate == 1) {
    digitalWrite(o0, LOW); // ON
    digitalWrite(o4, LOW); // ON

// --- RULE 1: METAL PRIORITY SORTING ---
    int scout_metal = digitalRead(s0); 
    int arrival_s1  = digitalRead(s1); 

    if (scout_metal == LOW) { 
      if (is_metal == 0) {
        Serial.println(">> MEMORY: METAL DETECTED (LATCHED)");
        is_metal = 1; 
      }
    }

    if (arrival_s1 == LOW) {
      if (is_metal >= 1) {
        digitalWrite(o1, HIGH); // OFF (Retract)
        is_metal = 2; 
      } 
      else {
        digitalWrite(o1, LOW); // ON (Fire/Kick)
      }
    } 
    else {
      digitalWrite(o1, HIGH); // OFF (Retract)
      
      if (is_metal == 2) {
        Serial.println(">> MEMORY: METAL CLEARED (RESET)");
        is_metal = 0; 
      }
    }
    
// --- RULE 2: INDEPENDENT FLOW CONTROL + DEBUG ---
    int scout = digitalRead(s9);   
    int feeder = digitalRead(s2);  

    static unsigned long lastDashboard = 0;
    if (current_time - lastDashboard > 500) {
      Serial.print("--- SENSORS --- S9(Scout): "); Serial.print(scout);
      Serial.print(" | S2(Feeder): "); Serial.print(feeder);
      Serial.print(" | State: "); Serial.println(r2_busy);
      lastDashboard = current_time;
    }

    if (r2_busy == 0) {
      if (scout == HIGH && first_ring == 0) { 
        Serial.println("DEBUG >> TRIGGER: S9 Detected Ring (HIGH)");
        r2_busy = 3; 
        r2_timer = current_time;
        first_ring ==1;
      }
      else if (scout == HIGH) { 
        Serial.println("DEBUG >> TRIGGER: S9 Detected Ring (HIGH)");
        r2_busy = 1; 
        r2_timer = current_time;
      } 
      else if (feeder == 1 && lastS2 == 0) {
        Serial.println("DEBUG >> TRIGGER: S2 Departure Detected (1 to 0)");
        r2_busy = 1;
        r2_timer = current_time;
      } 
    }

    if (r2_busy == 3) {
      digitalWrite(o2, HIGH); // Ensure closed while waiting
      // Uses the new tuning parameter for adjustable gate duration
      if (current_time - r2_timer > delay_before_open_ms){
        r2_busy = 1;
        r2_timer = current_time;
      }
    }

    if (r2_busy == 1) {
      digitalWrite(o2, LOW); // ON (Open)
      // Uses the new tuning parameter for adjustable gate duration
      if (current_time - r2_timer > rotary_open_ms) { 
        r2_busy = 2;
        r2_timer = current_time;
      }
    }

    if (r2_busy == 2) {
      digitalWrite(o2, HIGH); // OFF (Close)
      if (current_time - r2_timer > 800) { 
        r2_busy = 0; 
      }
    }

    lastS2 = feeder;

// --- RULE 3: STICKY INSPECTION ---
    int pegSensing = digitalRead(s3);  
    int ringSensing = digitalRead(s8); 

    if (pegSensing == 1 || ringSensing == 0) {
      if (pegSensing == 1 && ringSensing == 0) {
        if (inspection_complete == 0) {
          good_part_expiry = current_time + travel_time + sticker_duration;
          Serial.println(">> OK: GOOD ASSEMBLY DETECTED");
          inspection_complete = 1; 
        }
      }
    } 

    if (pegSensing == 0 && ringSensing == 1) {
      inspection_complete = 0; 
    }

    // 3. REJECTION TRIGGER (S5)
    if (digitalRead(s5) == 0) {
       if (current_time < good_part_expiry) {
         digitalWrite(o3, HIGH);  // OFF (Pass)
       } else {
         digitalWrite(o3, LOW); // ON (Reject)
       }
    } else {
       digitalWrite(o3, HIGH); // OFF
    }
  }
  else {
    // --- TRUE OFF STATE ---
    digitalWrite(o0, HIGH); digitalWrite(o1, HIGH); digitalWrite(o2, HIGH); 
    digitalWrite(o3, HIGH); digitalWrite(o4, HIGH); 
    assem = 0; is_metal = 0;
  }
}