int relay_pin = 8;
int ir_pin_1=2;
int ir_pin_2=3;

int ir_pin_check_1=9;
int ir_pin_check_2=7;


volatile byte toogle_on_off = 0;
volatile int toogle = 0;
volatile int delta = 10;

void setup()  {

  Serial.begin(9600); 
  pinMode(ir_pin_1,INPUT); 
  pinMode(ir_pin_2,INPUT); 

  pinMode(ir_pin_check_1,INPUT); 
  pinMode(ir_pin_check_2,INPUT); 

  pinMode(relay_pin, OUTPUT);
  digitalWrite(relay_pin, LOW);

  attachInterrupt(0, toogle_1, FALLING);
  attachInterrupt(1, toogle_2, FALLING);

}
void loop()  {
  if (toogle_on_off == 1 && toogle == 1){
    delay(delta);

    if ((digitalRead(ir_pin_1) == HIGH)) {// || ((digitalRead(ir_pin_check_1) == HIGH))) {
      toogle_on_off = 0;
      toogle = 0;
      return;
    }

    digitalWrite(relay_pin, !digitalRead(relay_pin));
    delay(1000);
    toogle_on_off = 0;
    toogle = 0;
  }

  if (toogle_on_off == 1 && toogle == 2){
    delay(delta);

    if ((digitalRead(ir_pin_2) == HIGH)){// || ((digitalRead(ir_pin_check_2) == HIGH))) {
      toogle_on_off = 0;
      toogle = 0;
      return;
    }

    digitalWrite(relay_pin, !digitalRead(relay_pin));
    delay(1000);
    toogle_on_off = 0;
    toogle = 0;
  }
}

void toogle_1() {
//  Serial.print(digitalRead(ir_pin_1));
//  Serial.print(digitalRead(ir_pin_check_1));
  if ((digitalRead(ir_pin_1) == LOW)){// && (digitalRead(ir_pin_check_1) == LOW)) {
    toogle_on_off = 1;
    toogle = 1;
    //Serial.println("toogle_1");
  }
}

void toogle_2() {
//  Serial.print(digitalRead(ir_pin_2));
//  Serial.println(digitalRead(ir_pin_check_2));
 if ((digitalRead(ir_pin_2) == LOW)){ //&& (digitalRead(ir_pin_check_2) == LOW)) {
    toogle_on_off = 1;
    toogle = 2;
    //Serial.println("toogle_2");
  }
}









