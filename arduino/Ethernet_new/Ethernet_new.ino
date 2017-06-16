#include <SPI.h>
#include <Ethernet.h>


byte mac[] = { 0x90, 0xA2, 0xDA, 0x0E, 0xFE, 0x40 };
IPAddress ip(192, 168, 1, 10);
EthernetServer server(80);  

String HTTP_req;          // stores the HTTP request

const byte branch_1 = 2;
const byte branch_2 = 3;
const byte branch_3 = 4;
const byte branch_4 = 5;
const byte branch_5 = 6;
const byte branch_6 = 7;
const byte branch_7 = 8;
const byte pump = 9;

byte branch_1_status=0;
byte branch_2_status=0;
byte branch_3_status=0;
byte branch_4_status=0;
byte branch_5_status=0;
byte branch_6_status=0;
byte branch_7_status=0;
byte pump_status=0;

const byte analog1=A0;
byte analog1_status=0;

const byte timers_count=9;
unsigned long int timers[timers_count];

void setup() {
  // Start Serial
  Serial.begin(115200);
  
  fill_up_timers_array();
  
  // Init all outputs
  pinMode(branch_1, OUTPUT);
  pinMode(branch_2, OUTPUT);
  pinMode(branch_3, OUTPUT);
  pinMode(branch_4, OUTPUT);
  pinMode(branch_5, OUTPUT);
  pinMode(branch_6, OUTPUT);
  pinMode(branch_7, OUTPUT);
  pinMode(pump, OUTPUT);
  
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


void loop() {
    EthernetClient client = server.available();  // try to get client

    if (client) { 
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
        
    //check_all_branches_timer();
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
      char* tmp; // will point behind the number
      long alert_time = strtol(alert_str.c_str(), &tmp, 10);

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
  timers[branch]=long(millis()+alert_time);
  
  byte pin = get_branch_pin(branch);
  
  digitalWrite(pin,HIGH);
  digitalWrite(pump, HIGH);
}

void off(byte branch){
  // Remove timers rule
  timers[branch]=0;
  
  byte pin = get_branch_pin(branch);

  digitalWrite(pin,LOW);
   
  if ( if_no_branch_active() ){
    digitalWrite(pump, LOW);
  }
}

void analog_status(){
  analog1_status=analogRead(analog1);
}

void branches_status(){
  branch_1_status = digitalRead(branch_1);
  branch_2_status = digitalRead(branch_2);
  branch_3_status = digitalRead(branch_3);
  branch_4_status = digitalRead(branch_4);
  branch_5_status = digitalRead(branch_5);
  branch_6_status = digitalRead(branch_6);
  branch_7_status = digitalRead(branch_7);
  pump_status = digitalRead(pump);
}

bool if_no_branch_active(){
  branches_status();
  
  if (branch_1_status==LOW and branch_2_status==LOW and branch_3_status==LOW and branch_4_status==LOW and branch_5_status==LOW
    and branch_6_status==LOW and branch_7_status==LOW){
    return true;
  }
  return false;
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
  if (i==4){
    return branch_4;
  }
  if (i==5){
    return branch_5;
  }
  if (i==6){
    return branch_6;
  }
  if (i==7){
    return branch_7;
  }
  if (i==8){
    return pump;
  }
}

String form_branch_status_json(){
    //update branch status
    branches_status();
    String res = "{";
    res = res + "\"1\":"+"\""+String(branch_1_status)+"\", ";
    res = res + "\"2\":"+"\""+String(branch_2_status)+"\", ";
    res = res + "\"3\":"+"\""+String(branch_3_status)+"\", ";
    res = res + "\"4\":"+"\""+String(branch_4_status)+"\", ";
    res = res + "\"5\":"+"\""+String(branch_5_status)+"\", ";
    res = res + "\"6\":"+"\""+String(branch_6_status)+"\", ";
    res = res + "\"7\":"+"\""+String(branch_7_status)+"\", ";
    res = res + "\"pump\":"+"\""+String(pump_status)+"\"}";

    return res;
}

String form_analog_pins_json(){
    //update analog status
    analog_status();
    String res = "{";
    res = res + "\"analog1\":"+"\""+String(analog1_status)+"\"}";
  
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
      if ( int(timers[i]-millis()) < 0  ){
        Serial.print(i);
        Serial.print(" ");
        Serial.print(timers[i]);
        Serial.print(" ");
        Serial.println("OFF");
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




