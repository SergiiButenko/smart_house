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
int arduino_status = 1;

int branch_1 = 2;
int branch_2 = 3;
int branch_3 = 5;
int branch_4 = 6;
int branch_5 = 8;
int pump = 7;

void setup(void)
{
  // Start Serial
  Serial.begin(115200);

  // Init all outputs
  pinMode(branch_1, OUTPUT);
  pinMode(branch_2, OUTPUT);
  pinMode(branch_3, OUTPUT);
  pinMode(branch_4, OUTPUT);
  pinMode(branch_5, OUTPUT);
  pinMode(pump, OUTPUT);


  // Init variables and expose them to REST API
  rest.variable("status",&arduino_status);

  // Function to be exposed
//  rest.function("branch1On",branch1On);
//  rest.function("branch2On",branch2On);
//  rest.function("branch3On",branch3On);
//  rest.function("branch4On",branch4On);
//  rest.function("branch5On",branch5On);
  
  rest.function("branch1Off",branch1Off);
  rest.function("branch2Off",branch2Off);
  rest.function("branch3Off",branch3Off);
  rest.function("branch4Off",branch4Off);
  rest.function("branch5Off",branch5Off);
//
//  rest.function("pumpOn",pumpOn);
//  rest.function("pumpOff",pumpOff);

  //rest.function("branches_status",branches_status);
  
  // Give name & ID to the device (ID should be 6 characters long)
  rest.set_id("008");
  rest.set_name("irrigation_peregonivka");

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


int test(){
  return 0;
}

// Custom function accessible by the API
int branch1On(){
  digitalWrite(branch_1, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_1);
}

int branch1Off(){
  digitalWrite(branch_1, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_1);
}

int branch2On(){
  digitalWrite(branch_2, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_2);
}

int branch2Off(){
  digitalWrite(branch_2, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_2);
}

int branch3On(){
  digitalWrite(branch_3, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_3);
}

int branch3Off(){
  digitalWrite(branch_3, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_3);
}

int branch4On(){
  digitalWrite(branch_4, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_4);
}

int branch4Off(){
  digitalWrite(branch_4, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_4);
}

int branch5On(){
  digitalWrite(branch_5, HIGH);
  digitalWrite(pump, HIGH);

  return digitalRead(branch_5);
}

int branch5Off(){
  digitalWrite(branch_5, LOW);
  digitalWrite(pump, LOW);

  return digitalRead(branch_5);
}

int pumpOn(){
  digitalWrite(pump, HIGH);

  return digitalRead(pump);
}


int pumpOff(){
  digitalWrite(pump, LOW);

  return digitalRead(pump);
}


//char branches_status(){
//  char res[6];
//  res[0]=digitalRead(branch_1);
//  res[1]=digitalRead(branch_2);
//  res[2]=digitalRead(branch_3);
//  res[3]=digitalRead(branch_4);
//  res[4]=digitalRead(branch_5);
//  res[5]=digitalRead(pump);
//
//  return res;
//}
