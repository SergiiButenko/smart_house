#include <SPI.h>
#include <Ethernet.h>


byte mac[] = { 0x90, 0xA2, 0xDA, 0x0E, 0xFE, 0x40 };
IPAddress ip(192, 168, 1, 10);
EthernetServer server(80);  

String HTTP_req;          // stores the HTTP request

const byte branch_1 = 22;
const byte branch_2 = 23;
const byte branch_3 = 24;
const byte branch_4 = 25;
const byte branch_5 = 26;
const byte branch_6 = 27;
const byte branch_7 = 28;
const byte branch_8 = 29;
const byte branch_9 = 30;
const byte branch_10 = 31;
const byte branch_11 = 32;
const byte branch_12 = 33;
const byte branch_13 = 34;
const byte branch_14 = 35;
const byte branch_15 = 36;
const byte branch_16 = 37;
const byte pump = 7;

byte branch_1_status=0;
byte branch_2_status=0;
byte branch_3_status=0;
byte branch_4_status=0;
byte branch_5_status=0;
byte branch_6_status=0;
byte branch_7_status=0;
byte branch_8_status=0;
byte branch_9_status=0;
byte branch_10_status=0;
byte branch_11_status=0;
byte branch_12_status=0;
byte branch_13_status=0;
byte branch_14_status=0;
byte branch_15_status=0;
byte branch_16_status=0;
byte pump_status=0;

const byte analog0=A0;
const byte analog1=A1;
const byte analog2=A2;
const byte analog3=A3;
const byte analog4=A4;
const byte analog5=A5;
const byte analog6=A6;
const byte analog7=A7;

byte analog0_status=0;
byte analog1_status=0;
byte analog2_status=0;
byte analog3_status=0;
byte analog4_status=0;
byte analog5_status=0;
byte analog6_status=0;
byte analog7_status=0;

//quantity of branches = branches + 1 since branch id starts from 1
const byte timers_count=17;
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
  pinMode(branch_8, OUTPUT);
  pinMode(branch_9, OUTPUT);
  pinMode(branch_10, OUTPUT);
  pinMode(branch_11, OUTPUT);
  pinMode(branch_12, OUTPUT);
  pinMode(branch_13, OUTPUT);
  pinMode(branch_14, OUTPUT);
  pinMode(branch_15, OUTPUT);
  pinMode(branch_16, OUTPUT);
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

//MAIN
void loop() {
    EthernetClient client = server.available();  // try to get client
      process_incoming_client(client);        
      check_all_branches_timer();
    
    process_incoming_weatcher_string();
}
//END MAIN

void process_incoming_weatcher_string(){
  return;
}

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
  digitalWrite(pump, HIGH);
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
  if ( if_no_branch_active() ){
    digitalWrite(pump, LOW);
  }
}

void analog_status(){
  analog0_status=analogRead(analog0);
  analog1_status=analogRead(analog1);
  analog2_status=analogRead(analog2);
  analog3_status=analogRead(analog3);
  analog4_status=analogRead(analog4);
  analog5_status=analogRead(analog5);
  analog6_status=analogRead(analog6);
  analog7_status=analogRead(analog7);
}

void branches_status(){
  branch_1_status = digitalRead(branch_1);
  branch_2_status = digitalRead(branch_2);
  branch_3_status = digitalRead(branch_3);
  branch_4_status = digitalRead(branch_4);
  branch_5_status = digitalRead(branch_5);
  branch_6_status = digitalRead(branch_6);
  branch_7_status = digitalRead(branch_7);
  branch_8_status = digitalRead(branch_8);
  branch_9_status = digitalRead(branch_9);
  branch_10_status = digitalRead(branch_10);
  branch_11_status = digitalRead(branch_11);
  branch_12_status = digitalRead(branch_12);
  branch_13_status = digitalRead(branch_13);
  branch_14_status = digitalRead(branch_14);
  branch_15_status = digitalRead(branch_15);
  branch_16_status = digitalRead(branch_16);
  pump_status = digitalRead(pump);
}

bool if_no_branch_active(){
  branches_status();
  
  if (branch_1_status==LOW and branch_2_status==LOW and branch_3_status==LOW and branch_4_status==LOW and branch_5_status==LOW
    and branch_6_status==LOW and branch_7_status==LOW and branch_8_status==LOW and branch_9_status==LOW and branch_10_status==LOW
    and branch_11_status==LOW and branch_12_status==LOW and branch_13_status==LOW and branch_14_status==LOW and branch_15_status==LOW
    and branch_16_status==LOW){
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
    return branch_8;
  }
  if (i==9){
    return branch_9;
  }
  if (i==10){
    return branch_10;
  }
  if (i==11){
    return branch_11;
  }
  if (i==12){
    return branch_12;
  }
  if (i==13){
    return branch_13;
  }
  if (i==14){
    return branch_14;
  }
  if (i==15){
    return branch_15;
  }
  if (i==16){
    return branch_16;
  }
  if (i==17){
    return pump;
  }
  return 0;
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
    res = res + "\"8\":"+"\""+String(branch_8_status)+"\", ";
    res = res + "\"9\":"+"\""+String(branch_9_status)+"\", ";
    res = res + "\"10\":"+"\""+String(branch_10_status)+"\", ";
    res = res + "\"11\":"+"\""+String(branch_11_status)+"\", ";
    res = res + "\"12\":"+"\""+String(branch_12_status)+"\", ";
    res = res + "\"13\":"+"\""+String(branch_13_status)+"\", ";
    res = res + "\"14\":"+"\""+String(branch_14_status)+"\", ";
    res = res + "\"15\":"+"\""+String(branch_15_status)+"\", ";
    res = res + "\"16\":"+"\""+String(branch_16_status)+"\", ";
    res = res + "\"pump\":"+"\""+String(pump_status)+"\"}";

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
    res = res + "\"analog5\":"+"\""+String(analog5_status)+"\", ";
    res = res + "\"analog6\":"+"\""+String(analog6_status)+"\", ";
    res = res + "\"analog7\":"+"\""+String(analog7_status)+"\"}";
  
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




