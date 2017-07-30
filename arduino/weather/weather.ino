#include <SPI.h>
#include <Ethernet.h>
#include "DHT.h"

#define DHTPIN 2 // номер пина, к которому подсоединен датчик
DHT dht(DHTPIN, DHT22);

byte mac[] = { 0x90, 0xA2, 0xDA, 0xFE, 0x0E, 0x40 };
IPAddress ip(192, 168, 1, 13);
EthernetServer server(80);  

String HTTP_req;          // stores the HTTP request

const byte branch_1 = 7;
const byte branch_2 = 5;
const byte branch_3 = 6;

byte branch_1_status=0;
byte branch_2_status=0;
byte branch_3_status=0;


const byte analog0=A0;
const byte analog1=A1;
const byte analog2=A2;
const byte analog3=A3;
const byte analog4=A4;
const byte analog5=A5;

byte analog0_status=0;
byte analog1_status=0;
byte analog2_status=0;
byte analog3_status=0;
byte analog4_status=0;
byte analog5_status=0;

//quantity of branches = branches + 1 since branch id starts from 1
const byte timers_count=4;
unsigned long int timers[timers_count];

float h = 0;
float t = 0;
boolean rain = false;
int daylight_0 = 0;
int daylight_1 = 0;

void setup() {
  // Start Serial
  Serial.begin(115200);
  
  fill_up_timers_array();
  
  // Init all outputs
  pinMode(branch_1, OUTPUT);
  pinMode(branch_2, OUTPUT);
  pinMode(branch_3, OUTPUT);

  pinMode(analog0, INPUT);
  pinMode(analog1, INPUT);
  pinMode(analog2, INPUT);
  pinMode(analog3, INPUT);
  pinMode(analog4, INPUT);
  pinMode(analog5, INPUT);
  
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

  dht.begin();
}

//MAIN
void loop() {
    EthernetClient client = server.available();  // try to get client
      process_incoming_client(client);        
      check_all_branches_timer();
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


void process_request(EthernetClient cl) {
    String host = get_host_from_request(HTTP_req);
    String data="";
    
    if (HTTP_req.indexOf("/favicon.ico") > -1) { 
      return;
    }
    
    if (HTTP_req.indexOf("/branch_status") > -1) { 
      data = form_branch_status_json();
      send_data_to_client(cl, host, data);
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
      data = form_branch_status_json();
      send_data_to_client(cl, host, data);
      return;
    }

    if (HTTP_req.indexOf("/branch_off") > -1) { 
      byte id_start = HTTP_req.indexOf("branch_id=");
      byte id_end = HTTP_req.indexOf(" HTTP/1.1");
      String id_str = HTTP_req.substring(id_start+10, id_end);
      byte branch_id=id_str.toInt();
      
      off(branch_id);
      delay(1);
      data = form_branch_status_json();
      send_data_to_client(cl, host, data);
      return;
    }

    if (HTTP_req.indexOf("/analog") > -1) { 
      data = form_analog_pins_json();
      send_data_to_client(cl, host, data);
      return;
    }

    if (HTTP_req.indexOf("/weather") > -1) { 
      data = form_weather_status_json();
      send_data_to_client(cl, host, data);
      return;
    }
    
    data = form_branch_status_json();
    send_data_to_client(cl, host, data);
    return;
}

void send_data_to_client(EthernetClient client, String host, String data){
  // Send request
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Host: " + host);
  client.println("Connection: close");
  client.print("Content-Length: ");
  client.println(data.length());
  client.println();
  client.print(data);
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

void analog_status(){
  analog0_status=smooth_read(analog0);
  analog1_status=smooth_read(analog1);
  analog2_status=smooth_read(analog2);
  analog3_status=smooth_read(analog3);
  analog4_status=smooth_read(analog4);
  analog5_status=smooth_read(analog5);
}

int smooth_read(int pin){
    byte num_reads = 10;
    int sum = 0;
    int avr = 0;
      for (byte i = 0; i < num_reads; i++) {
      sum = sum + analogRead(pin);
      delay(50);
      }
    
    avr = sum / num_reads;
    
    return avr;
}

void branches_status(){
  branch_1_status = digitalRead(branch_1);
  branch_2_status = digitalRead(branch_2);
  branch_3_status = digitalRead(branch_3);
}


byte get_branch_pin(byte i){
  if (i==1){
    return branch_1;
  }
  if (i==2){
    return branch_2;
  }
  if (i==3){
    return branch_3;
  }

  return 0;
}

String form_branch_status_json(){
    //update branch status
    branches_status();
    String res = "{";
    res = res + "\"1\":"+"\""+String(branch_1_status)+"\", ";
    res = res + "\"2\":"+"\""+String(branch_2_status)+"\", ";
    res = res + "\"3\":"+"\""+String(branch_3_status)+"\"}";

    return res;
}

String form_analog_pins_json(){
    //update analog status
    analog_status();
    String res = "{";
    res = res + "\"analog0\":"+"\""+String(analog0_status)+"\", ";
    res = res + "\"analog1\":"+"\""+String(analog1_status)+"\", ";
    res = res + "\"analog2\":"+"\""+String(analog2_status)+"\", ";
    res = res + "\"analog3\":"+"\""+String(analog3_status)+"\", ";
    res = res + "\"analog4\":"+"\""+String(analog4_status)+"\", ";
    res = res + "\"analog5\":"+"\""+String(analog5_status)+"\"}"; 
    
    Serial.println(res);
    return res;
}


String form_weather_status_json(){
    h = dht.readHumidity();
    t = dht.readTemperature();
    
    //update analog pins
    analog_status();
    if (isnan(h) || isnan(t)) {
      h = 0;
      t = 0;
    }
    String res = "{";
    res = res + "\"temperature\":" +"\""+String(t)+"\", ";
    res = res + "\"humidity_air\":"+"\""+String(h)+"\", ";
    res = res + "\"humidity_earth\":"+"\""+String(analog2_status)+"\", ";
    res = res + "\"daylight0\":"+"\""+String(analog0_status)+"\", ";
    res = res + "\"daylight1\":"+"\""+String(analog1_status)+"\", ";
    res = res + "\"rain\":"+"\""+String(rain)+"\"}";
    Serial.println(res);
    return res;
}

String get_host_from_request(String request){
  return "192.168.1.143";
}


void check_all_branches_timer(){
  for (byte i = 0; i < timers_count; i++) {
    if (timers[i]==0){
      continue;
    } else {
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




