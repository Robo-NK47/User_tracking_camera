#include<Servo.h>

Servo HorizontalServo;
Servo VerticalServo;
int incoming[1];

void setup()
{
HorizontalServo.attach(4);
VerticalServo.attach(3);
Serial.begin(9600);

HorizontalServo.write(90);
VerticalServo.write(45);
}

void loop(){
  while(Serial.available() >= 2){
    // fill array
    for (int i = 0; i < 2; i++)
    {
      incoming[i] = Serial.read();
    }
    // use the values
    HorizontalServo.write(incoming[0]);
    VerticalServo.write(incoming[1]);
  }
}
