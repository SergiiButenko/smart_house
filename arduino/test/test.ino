/*
 Input Pullup Serial
 
 This example demonstrates the use of pinMode(INPUT_PULLUP). It reads a 
 digital input on pin 2 and prints the results to the serial monitor.
 
 The circuit: 
 * Momentary switch attached from pin 2 to ground 
 * Built-in LED on pin 13
 
 Unlike pinMode(INPUT), there is no pull-down resistor necessary. An internal 
 20K-ohm resistor is pulled to 5V. This configuration causes the input to 
 read HIGH when the switch is open, and LOW when it is closed. 
 
 created 14 March 2012
 by Scott Fitzgerald
 
 http://www.arduino.cc/en/Tutorial/InputPullupSerial
 
 This example code is in the public domain
 
 */
void inverse_levels(){
  for (int thisPin = 22; thisPin <= 50; thisPin = thisPin + 2)  {
    int pin = thisPin+1;
    int in = digitalRead(pin);
    if (in == HIGH){
      digitalWrite(thisPin, LOW);
    } else {
      digitalWrite(thisPin, HIGH);
    }
    delay(1);
  }
}

void setup(){
  //start serial connection
  Serial.begin(9600);
  //configure pin2 as an input and enable the internal pull-up resistor
  
  for (int thisPin = 22; thisPin <= 50; thisPin=thisPin + 2)  {
    pinMode(thisPin, OUTPUT);
    pinMode(thisPin+1, INPUT_PULLUP);
  }

}

void loop(){
  inverse_levels();
  
  Serial.print(digitalRead(23));
  Serial.println(digitalRead(22));
  delay(10);
}



