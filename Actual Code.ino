unsigned long curr_time = 0;
unsigned long time1 = 0;
unsigned long time2 = 0;
unsigned long time3 = 0;
unsigned long time4 = 0;
unsigned long time5 = 0;
const int delay1 = 2000;
const int delay2 = 1000;
const int delay3 = 1500;
const int delay4 = 500;
const int delay5 = 500; //assem no
int on1 = 0;
int on2 = 0;
int on3 = 0;
int on4 = 0;
int on5 = 0;
int ring = 0;
int assem = 0;
int onstate = 0;

int s0 = 22;
int s1 = 23;
int s2 = 26;
int s3 = 27;
int s4 = 30;
int s5 = 31;
int s6 = 34;
int s7 = 35;
int s8 = 38;
int s9 = 8;
int s10 = 7;
int o0 = 2;
int o1 = 3;
int o2 = 4;
int o3 = 5;
int o4 = 6;


void setup() {
  Serial.begin(9600);
  pinMode(s0, INPUT);
  pinMode(s1, INPUT);
  pinMode(s2, INPUT);
  pinMode(s3, INPUT);
  pinMode(s4, INPUT);
  pinMode(s5, INPUT);
  pinMode(s6, INPUT);
  pinMode(s7, INPUT);
  pinMode(s8, INPUT);
  pinMode(s9, INPUT);
  pinMode(s10, INPUT);
  pinMode(o0, OUTPUT);
  pinMode(o1, OUTPUT);
  pinMode(o2, OUTPUT);
  pinMode(o3, OUTPUT);
  pinMode(o4, OUTPUT);
}

void loop() {

//on state
if(digitalRead(s6) == HIGH && digitalRead(s7) == LOW){
onstate = 1;
}
if(digitalRead(s6) == LOW && digitalRead(s7) == HIGH){
onstate = 0;
}

if(onstate == 1){
//conveyer chain
analogWrite(o0 , 100);
analogWrite(o4 , 100);

//timer
  if(millis() - curr_time >= 100){
   curr_time = millis();
   
  }

//upper part
if(digitalRead(s1) == HIGH && digitalRead(s0) == LOW && ring < 6 && curr_time - time1 >= delay1){
analogWrite(o1 , 100);
on1 = 1;
}
if(digitalRead(s9) == HIGH && on1 == 1){
time1 = curr_time;
ring += 1;
Serial.println(ring);
on1 = 0;
}
if( curr_time - time1 >= delay1){
analogWrite(o1 , 0);
}

//ring part
if( curr_time - time4 >= delay4 && on3 == 1){
analogWrite(o2 , 0);
on3 = 0;
}
if(digitalRead(s2) == LOW && curr_time - time2 >= delay2 && ring > 0 && on2 == 1){
analogWrite(o2 , 100);
ring -= 1;
Serial.println(ring);
time4 = curr_time;
on3 = 1;
}
if(digitalRead(s2) == LOW && ring > 0 && curr_time - time2 >= delay2){
time2 = curr_time;
on2 = 1;
}


//assem part(assem=yes)
if(digitalRead(s3) == HIGH && digitalRead(s8) == HIGH){
assem = 1;
}
if(digitalRead(s5) == HIGH && assem == 1 && on4 == 0){
time3 = curr_time;
on4 = 1;
}
if(digitalRead(s5) == LOW && curr_time - time3 >= delay3 && on4 == 1){
assem = 0;
on4 = 0;
}

//assem part(assem=no)
if(digitalRead(s5) == HIGH && assem == 0 && on5 == 0){
analogWrite(o3 , 100);
time5 = curr_time;
on5 = 1;
}
if(digitalRead(s10) == HIGH && curr_time - time5 >= delay5 && on5 == 1){
analogWrite(o3 , 0);
on5 = 0;
}

}else{//off state
digitalWrite(o0 , LOW); //coveyer chain
digitalWrite(o4 , LOW); //coveyer chain
}
}