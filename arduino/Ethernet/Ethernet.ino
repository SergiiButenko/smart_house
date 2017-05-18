/*
  This a simple example of the aREST Library for Arduino (Uno/Mega/Due/Teensy)
  using the Ethernet library (for example to be used with the Ethernet shield).
  See the README file for more details.

  Written in 2014 by Marco Schwartz under a GPL license.
*/

// Libraries
#include <SPI.h>
#include <Ethernet.h>
#include <aREST.h>
#include <avr/wdt.h>

// Enter a MAC address for your controller below.
byte mac[] = { 0x90, 0xA2, 0xDA, 0x0E, 0xFE, 0x40 };

// IP address in case DHCP fails
IPAddress ip(192,168,1,2);

// Ethernet server
EthernetServer server(80);

// Create aREST instance
aREST rest = aREST();

// Variables to be exposed to the API
int arduino_status;

int brach_1 = 2;
int brach_2 = 3;
int brach_3 = 5;
int brach_4 = 6;
int brach_5 = 8;
int pump = 7;

void setup(void)
{
  // Start Serial
  Serial.begin(115200);

  // Init all outputs
  pinMode(brach_1, OUTPUT);
  pinMode(brach_2, OUTPUT);
  pinMode(brach_3, OUTPUT);
  pinMode(brach_4, OUTPUT);
  pinMode(brach_5, OUTPUT);
  pinMode(pump, OUTPUT);


  // Init variables and expose them to REST API
  rest.variable("status",&arduino_status);

  // Function to be exposed
  rest.function("branch_1_on",branch_1_on);
  rest.function("branch_2_on",branch_2_on);
  rest.function("branch_3_on",branch_3_on);
  rest.function("branch_4_on",branch_4_on);
  rest.function("branch_5_on",branch_5_on);

  rest.function("branch_1_off",branch_1_off);
  rest.function("branch_2_off",branch_2_off);
  rest.function("branch_3_off",branch_3_off);
  rest.function("branch_4_off",branch_4_off);
  rest.function("branch_5_off",branch_5_off);

  rest.function("pump_on",pump_on);
  rest.function("pump_off",pump_off);

  rest.function("branches_status",branches_status);

  // Give name & ID to the device (ID should be 6 characters long)
  rest.set_id("001");
  rest.set_name("irrifation_peregonivka");

  // Start the Ethernet connection and the server
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    // no point in carrying on, so do nothing forevermore:
    // try to congifure using IP address instead of DHCP:
    Ethernet.begin(mac, ip);
  }
  server.begin();
  Serial.print("server is at ");
  Serial.println(Ethernet.localIP());

  // Start watchdog
  wdt_enable(WDTO_4S);
}

void loop() {
  // listen for incoming clients
  EthernetClient client = server.available();
  rest.handle(client);
  wdt_reset();
}



// Custom function accessible by the API
int branch_1_on(){
  digitalWrite(branch_1, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_1);
}

int branch_1_off(){
  digitalWrite(branch_1, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_1);
}

int branch_2_on(){
  digitalWrite(branch_2, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_2);
}

int branch_2_off(){
  digitalWrite(branch_2, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_2);
}

int branch_3_on(){
  digitalWrite(branch_3, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_3);
}


int branch_3_off(){
  digitalWrite(branch_3, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_3);
}

int branch_4_on(){
  digitalWrite(branch_4, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_4);
}

int branch_4_off(){
  digitalWrite(branch_4, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_4);
}

int branch_5_on(){
  digitalWrite(branch_5, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_5);
}

int branch_5_off(){
  digitalWrite(branch_5, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_5);
}

int pump_on(){
  digitalWrite(pump, HIGH);

  return digitalRead(pump);
}


int pump_off(){
  digitalWrite(pump, LOW);

  return digitalRead(pump);
}


char[] branches_status(){
  char res[6];
  res[0]=digitalRead(branch_1);
  res[1]=digitalRead(branch_2);
  res[2]=digitalRead(branch_3);
  res[3]=digitalRead(branch_4);
  res[4]=digitalRead(branch_5);
  res[5]=digitalRead(pump);

  return res;
}
