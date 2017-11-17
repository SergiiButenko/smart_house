int relay_pin = 13;
int ir_pin=2;

void setup()  {
 Serial.begin(9600);
 pinMode(ir_pin,INPUT);
 pinMode(relay_pin, OUTPUT);
}

void loop()  {
 delay(1);
 if (digitalRead(ir_pin) == LOW) {
	digitalWrite(relay_pin, !digitalRead(relay_pin));
	delay(1000); 	
 }
}

