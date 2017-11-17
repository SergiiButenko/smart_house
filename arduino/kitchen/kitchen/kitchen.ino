int relay_pin = 13;
int ir_pin=2;
volatile byte state = LOW;

void setup()  {

 Serial.begin(9600); //Start serial communication boud rate at 9600
 pinMode(ir_pin,INPUT); //Pin 5 as signal input
 pinMode(relay_pin, OUTPUT);
 
 attachInterrupt(1, blink, FALLING);

}
void loop()  {
 delay(750);
 digitalWrite(relay_pin, state);
}

void blink() {
  state = !state;
}


