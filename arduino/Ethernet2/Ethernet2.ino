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
int branch_1_status;
int branch_2_status;
int branch_3_status;
int branch_4_status;
int branch_5_status;
int pump_status;

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
 
rest.variable("1",&branch_1_status);
rest.variable("2",&branch_2_status);
rest.variable("3",&branch_3_status);
rest.variable("4",&branch_4_status);
rest.variable("5",&branch_5_status);
rest.variable("pump",&pump_status);  


  // Function to be exposed
  rest.function("on",on);
  rest.function("off",off);
  
  // Give name & ID to the device (ID should be 6 characters long)
  rest.set_id("008");
  rest.set_name("name");

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

void branches_status(){
  branch_1_status = digitalRead(branch_1);
  branch_2_status = digitalRead(branch_2);
  branch_3_status = digitalRead(branch_3);
  branch_4_status = digitalRead(branch_4);
  branch_5_status = digitalRead(branch_5);
  pump_status = digitalRead(pump);
}

bool if_no_branch_active(){
  if (branch_1_status==LOW and branch_2_status==LOW and branch_3_status==LOW and branch_4_status==LOW and branch_5_status==LOW){
    return true;
  }
  return false;
}

int get_branch_pin(int i){
  if (i==1){
    return branch_1;
  }
  if (i==2){
    return branch_2;
  }
  if (i==3){
    return branch_3;
  }
  if (i==4){
    return branch_4;
  }
  if (i==5){
    return branch_5;
  }
  if (i==7){
    return pump;
  }
}

int on(String branch){
  // Get state from command
  int pin = get_branch_pin(branch.toInt());
  Serial.println(pin);
  digitalWrite(pin,HIGH);
  digitalWrite(pump, HIGH);

  branches_status();
  return digitalRead(pin);
}

int off(String branch){
  // Get state from command
  int pin = get_branch_pin(branch.toInt());

  digitalWrite(pin,LOW);
  branches_status();
  
  if ( if_no_branch_active() ){
    digitalWrite(pump, LOW);
  }

  branches_status();
  return digitalRead(pin);
}
