int relay_pin = 4;
int ir_pin=2;
volatile byte toogle_on_off = 0;

void setup()  {

 Serial.begin(9600); //Start serial communication boud rate at 9600
 pinMode(ir_pin,INPUT); //Pin 5 as signal input
 pinMode(relay_pin, OUTPUT);
 
 attachInterrupt(1, toogle, FALLING);

}
void loop()  {
  if (toogle_on_off == 1){
   delay(500);
   digitalWrite(relay_pin, !digitalRead(relay_pin));
  toogle_on_off = 0;
  }
}

void toogle() {
  toogle_on_off = 1;
}


