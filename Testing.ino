int IP0 = 22;
int IP1 = 23;
int IP2 = 24;
int IP3 = 25;
int IP4 = 26;
int IP5 = 27;
int IP6 = 28;
int IP7 = 29;
int IP8 = 30;
int IP9 = 31;
int IP10 = 32;

void setup() {
  Serial.begin(9600);
  pinMode(IP0, INPUT);
  pinMode(IP1, INPUT);
  pinMode(IP2, INPUT);
  pinMode(IP3, INPUT);
  pinMode(IP4, INPUT);
  pinMode(IP5, INPUT);
  pinMode(IP6, INPUT);
  pinMode(IP7, INPUT);
  pinMode(IP8, INPUT);
  pinMode(IP9, INPUT);
  pinMode(IP10, INPUT);
}

void loop() {
  if (digitalRead(IP0) == HIGH){
    Serial.println("IP0");
  }
  if (digitalRead(IP1) == HIGH){
    Serial.println("IP1");
  }
  if (digitalRead(IP2) == HIGH){
    Serial.println("IP2");
  }
  if (digitalRead(IP3) == HIGH){
    Serial.println(digitalRead(IP3));
  }
  if (digitalRead(IP4) == HIGH){
    Serial.println("IP4");
  }
  if (digitalRead(IP5) == HIGH){
    Serial.println("IP5");
  }
  if (digitalRead(IP6) == HIGH){
    Serial.println("IP6");
  }
  if (digitalRead(IP7) == HIGH){
    Serial.println("IP7");
  }
  if (digitalRead(IP8) == HIGH){
    Serial.println("IP8");
  }
  if (digitalRead(IP9) == HIGH){
    Serial.println("IP9");
  }
  if (digitalRead(IP10) == HIGH){
    Serial.println("IP10");
  }
  
}
