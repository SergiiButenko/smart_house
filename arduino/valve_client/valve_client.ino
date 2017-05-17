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
int status_arduino;

void setup(void)
{
  // Start Serial
  Serial.begin(115200);
    
//  pinMode(2, OUTPUT);
//  pinMode(3, OUTPUT);
//  
//  pinMode(5, OUTPUT);
//  pinMode(6, OUTPUT);
//  pinMode(7, OUTPUT);
//  pinMode(8, OUTPUT);
  
  // Init variables and expose them to REST API
  status_arduino = 1;
  rest.variable("status",&status_arduino);

  // Function to be exposed
  rest.function("branch2_on",branch2_on);
  rest.function("branch3_on",branch3_on);
  rest.function("branch4_on",branch4_on);
  rest.function("branch5_on",branch5_on);
  rest.function("branch6_on",branch6_on);
  rest.function("pump_on",pump_on);
 
  rest.function("branch2_off",branch2_off);
  rest.function("branch3_off",branch3_off);
  rest.function("branch4_off",branch4_off);
  rest.function("branch5_off",branch5_off);
  rest.function("branch6_off",branch6_off);
  rest.function("pump_off",pump_off);

  //  rest.function("branch_status",branch_status);

  // Give name & ID to the device (ID should be 6 characters long)
  rest.set_id("001");
  rest.set_name("branch_controller");

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
  int pump_on(){
    digitalWrite(7, HIGH);
    return digitalRead(7);
  }
  
  int on(int pin){
    digitalWrite(pin, HIGH);
    pump_on();
    
    return digitalRead(pin);
  }
  
  int branch2_on(){
    return on(2);
  }

  int branch3_on(){
    return on(3);
  }

  int branch4_on(){
    return on(8);
  }

  int branch5_on(){
    return on(5);
  }

  int branch6_on(){
    return on(6);
  }
  

  int pump_off(){
    digitalWrite(7, LOW);
    return digitalRead(7);
  }

  int off(int pin){
    digitalWrite(pin, LOW);
    pump_off();
    
    return digitalRead(pin);
  }
  
  int branch1_off(){
    return off(1);
  }
  
  int branch2_off(){
    return off(2);
  }

  int branch3_off(){
    return off(3);
  }

  int branch4_off(){
    return off(8);
  }

  int branch5_off(){
    return off(5);
  }

  int branch6_off(){
    return off(6);
  }
  
  char branch_status(){
    char branch_status[7];
      branch_status[2] = digitalRead(2);
      branch_status[3] = digitalRead(3);
      branch_status[4] = digitalRead(4);
      branch_status[5] = digitalRead(5);
      branch_status[6] = digitalRead(6);
      branch_status[7] = digitalRead(7);
    return branch_status;
  }

