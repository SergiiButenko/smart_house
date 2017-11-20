int relay_pin = 12;
int ir_pin=2;
volatile byte toogle_on_off = 0;

void setup()  {

  Serial.begin(9600); //Start serial communication boud rate at 9600
  pinMode(ir_pin,INPUT_PULLUP); //Pin 5 as signal input
  pinMode(relay_pin, OUTPUT);
  digitalWrite(relay_pin, LOW);

  attachInterrupt(0, toogle, RISING);

}
void loop()  {
  if (toogle_on_off == 1){
    Serial.println("on");
    digitalWrite(relay_pin, !digitalRead(relay_pin));
    toogle_on_off = 0;
    delay(1000);
    toogle_on_off = 0;
  }
}

void toogle() {
  toogle_on_off = 1;
}



