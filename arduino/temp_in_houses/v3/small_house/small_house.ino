#include <SPI.h>
#include <Ethernet.h>
#include <DHT.h>
#include <ICMPPing.h>

void(* resetFunc) (void) = 0; //declare reset function @ address 0

byte mac[] = { 
  0x90, 0xA2, 0x40, 0x0E, 0xFE, 0xDA};
IPAddress ip(192, 168, 1, 11);

IPAddress pingAddr(192,168,1,1); // ip address to ping
SOCKET pingSocket = 0;
char buffer [256];
ICMPPing ping(pingSocket, (uint16_t)random(0, 255));

EthernetServer server(80);  

String HTTP_req;          // stores the HTTP request

// Power outlet 1rst flor
const byte branch_1 = 2;
const byte branch_2 = 3;

// Heat
const byte branch_3 = 5;

// Power outlet 2nd flor
const byte branch_4 = 6;
const byte branch_5 = 7;


#define DHTTYPE DHT22   // DHT 22  (AM2302)
// DHT 1flor
#define DHTPIN_FIRST 8     // what pin we're connected to
DHT dht_first(DHTPIN_FIRST, DHTTYPE);

// DHT 2flor
#define DHTPIN_SECOND 9     // what pin we're connected to
DHT dht_second(DHTPIN_SECOND, DHTTYPE);


byte branch_1_status=0;
byte branch_2_status=0;
byte branch_3_status=0;
byte branch_4_status=0;
byte branch_5_status=0;

//quantity of branches = branches + 1 since branch id starts from 1
const byte timers_count=30;
unsigned long int timers[timers_count];

unsigned long previousMillis_ping = 0;
long interval_ping = 60000;

void setup() {
  // Start Serial
  Serial.begin(115200);

  // disable SD card
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);

  dht_first.begin();
  dht_second.begin();

  fill_up_timers_array();

  // Init all outputs
  pinMode(branch_1, OUTPUT);
  pinMode(branch_2, OUTPUT);
  pinMode(branch_3, OUTPUT);
  pinMode(branch_4, OUTPUT);
  pinMode(branch_5, OUTPUT);

  // Disable SD SPI
  pinMode(4,OUTPUT);
  digitalWrite(4,HIGH);

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
}

//MAIN
void loop() {
  EthernetClient client = server.available();  // try to get client
  process_incoming_client(client);        
  check_all_branches_timer();
  ping_60_sec();
}
//END MAIN


void process_incoming_client(EthernetClient client){
  if (!client) 
    return;

  boolean currentLineIsBlank = true;
  while (client.connected()) {
    if (client.available()) {   
      char c = client.read(); // read 1 byte (character) from client
      HTTP_req += c; 
      // last line of client request is blank and ends with \n
      // respond to client only after last line received
      if (c == '\n' && currentLineIsBlank) {
        process_request(client);
        HTTP_req = "";
        break;
      }
      // every line of text received from the client ends with \r\n
      if (c == '\n') {
        // last character on line of received text
        // starting new line with next character read
        currentLineIsBlank = true;
      } 
      else if (c != '\r') {
        currentLineIsBlank = false;
      }
    } 
  } 
  delay(1);      // give the web browser time to receive the data
  client.stop(); 

}


void process_request(EthernetClient cl_renamed) {
  Serial.println(HTTP_req);


  if (HTTP_req.indexOf("/favicon.ico") > -1) { 
    return;
  }

  if (HTTP_req.indexOf("/branch_status") > -1) { 
    // response header
    data = form_branch_status_json();
    send_data_to_client(cl_renamed, host, data);
    return;
  }

  if (HTTP_req.indexOf("/branch_on") > -1) { 
    byte id_start = HTTP_req.indexOf("branch_id=");
    byte id_end = HTTP_req.indexOf("&");
    String id_str = HTTP_req.substring(id_start+10, id_end);
    byte branch_id=id_str.toInt();

    byte alert_start = HTTP_req.indexOf("branch_alert=");
    byte alert_end = HTTP_req.indexOf(" HTTP/1.1");
    String alert_str = HTTP_req.substring(alert_start+13, alert_end);
    byte alert_time=alert_str.toInt();

    on(branch_id, alert_time);
    delay(1);
    send_data_to_client(cl_renamed);
    return;
  }

  if (HTTP_req.indexOf("/branch_off") > -1) { 
    byte id_start = HTTP_req.indexOf("branch_id=");
    byte id_end = HTTP_req.indexOf(" HTTP/1.1");
    String id_str = HTTP_req.substring(id_start+10, id_end);
    byte branch_id=id_str.toInt();

    off(branch_id);
    send_data_to_client(cl_renamed);
    return;
  }

  if (HTTP_req.indexOf("/temperature") > -1) { 
    // start sensor reading
    // response header
    cl_renamed.println("HTTP/1.1 200 OK");
    cl_renamed.println("Content-Type: application/json");  // JSON response type
    cl_renamed.println("Connection: close");               // close connection after response
    cl_renamed.println();
    // open JSON
    cl_renamed.print("{");
    // temperature
    cl_renamed.print("\"1_floor_temperature\":\"");
    //    cl_renamed.print(dht_first.readTemperature());
    cl_renamed.print("22.00");
    cl_renamed.print("\"");
    // humidity
    cl_renamed.print(",\"1_floor_humidity\":\"");
    //    cl_renamed.print(dht_first.readHumidity());
    cl_renamed.print("22.00");
    cl_renamed.print("\"");
    cl_renamed.print(",\"2_floor_temperature\":\"");
    //    cl_renamed.print(dht_second.readTemperature());
    cl_renamed.print("22.00");
    cl_renamed.print("\"");
    // humidity
    cl_renamed.print(",\"2_floor_humidity\":\"");
    //    cl_renamed.print(dht_second.readHumidity());
    cl_renamed.print("22.00");
    cl_renamed.print("\"");
    // close json
    cl_renamed.println("}");    
    return;
  }

  send_data_to_client(cl_renamed);
  return;
}

void send_data_to_client(EthernetClient cl_renamed){
  // Send request
  cl_renamed.println("HTTP/1.1 200 OK");
  cl_renamed.println("Content-Type: application/json");  // JSON response type
  cl_renamed.println("Connection: close");               // close connection after response
  cl_renamed.println();
  // open JSON
  cl_renamed.print("{");

  cl_renamed.print("\"20\":\"");
  cl_renamed.print(digitalRead(branch_1));
  cl_renamed.print("\"");

  cl_renamed.print(",\"21\":\"");
  cl_renamed.print(digitalRead(branch_2));
  cl_renamed.print("\"");

  cl_renamed.print(",\"22\":\"");
  cl_renamed.print(digitalRead(branch_3));
  cl_renamed.print("\"");

  cl_renamed.print(",\"23\":\"");
  cl_renamed.print(digitalRead(branch_4));
  cl_renamed.print("\"");

  cl_renamed.print(",\"24\":\"");
  cl_renamed.print(digitalRead(branch_5));
  cl_renamed.print("\"");  

  // close json
  cl_renamed.println("}");
}

// turn on off logic
void on(byte branch, int alert_time){
  // Add timers rule
  if (branch < timers_count){
    timers[branch] = long(millis() / 60000 + alert_time);
  }

  byte pin = get_branch_pin(branch);
  if (pin==0){
    return;
  }

  digitalWrite(pin,HIGH);

}

void off(byte branch){
  // Remove timers rule
  if (branch < timers_count){
    timers[branch]=0;
  }

  byte pin = get_branch_pin(branch);  
  if (pin!=0){
    digitalWrite(pin,LOW);
  }
}

byte get_branch_pin(byte i){
  if (i==20){
    return branch_1;
  }

  if (i==21){
    return branch_2;
  }

  if (i==22){
    return branch_3;
  }

  if (i==23){
    return branch_4;
  }

  if (i==24){
    return branch_5;
  }

  return 0;
}

void check_all_branches_timer(){
  for (byte i = 0; i < timers_count; i++) {
    if (timers[i]==0){
      continue;
    } 
    else {
      if ( int(timers[i] - millis() / 60000) < 0  ){
        off(i); 
      }
    }
  }
}

void fill_up_timers_array(){
  for (byte i = 0; i > timers_count; i++) {
    timers[i]=0;
  }
}

void ping_60_sec(){
  unsigned long currentMillis_ping = millis();

  if(currentMillis_ping - previousMillis_ping > interval_ping) {
    // save the last time you blinked the LED 
    previousMillis_ping = currentMillis_ping;
    ICMPEchoReply echoReply = ping(pingAddr, 4);
    if (echoReply.status == SUCCESS)
    {
      sprintf(buffer,
      "Reply[%d] from: %d.%d.%d.%d: bytes=%d time=%ldms TTL=%d",
      echoReply.data.seq,
      echoReply.addr[0],
      echoReply.addr[1],
      echoReply.addr[2],
      echoReply.addr[3],
      REQ_DATASIZE,
      millis() - echoReply.data.time,
      echoReply.ttl);
      Serial.println(buffer);
    }
    else
    {
      sprintf(buffer, "Echo request failed; %d", echoReply.status);
      Serial.println(buffer);
      //resetFunc();  //call reset
      Serial.println("Reset doens't work");
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

    }
  }

}



