int relay_pin = 12;
int ir_pin=2;
volatile byte toogle_on_off = 0;
volatile int delta = 50;

void setup()  {

  Serial.begin(9600); //Start serial communication boud rate at 9600
  //  pinMode(ir_pin,INPUT); //Pin 5 as signal input
  pinMode(relay_pin, OUTPUT);
  digitalWrite(relay_pin, HIGH);

  attachInterrupt(0, toogle, FALLING);

}
void loop()  {
  if (toogle_on_off == 1){
    delay(delta);

    if (digitalRead(ir_pin) == HIGH){
      toogle_on_off = 0;
      return;
    }

    digitalWrite(relay_pin, !digitalRead(relay_pin));
    delay(1000);
    toogle_on_off = 0;
  }
}

void toogle() {
  if (digitalRead(ir_pin) == LOW){
    toogle_on_off = 1;
  }
}










