#include <SPI.h>
#include <Ethernet.h>
#include <DHT.h>


byte mac[] = { 
  0x90, 0xA2, 0x40, 0x0E, 0xFE, 0xDA};
IPAddress ip(192, 168, 1, 11);
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
const byte timers_count=8;
unsigned long int timers[timers_count];

void setup() {
  //  delay(60 * 1000);

  // Start Serial
  Serial.begin(115200);

  dht_first.begin();
  dht_second.begin();

  fill_up_timers_array();

  // Init all outputs
  pinMode(branch_1, OUTPUT);
  pinMode(branch_2, OUTPUT);
  pinMode(branch_3, OUTPUT);
  pinMode(branch_4, OUTPUT);
  pinMode(branch_5, OUTPUT);

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

  if (HTTP_req.indexOf("/temperature") > -1) { 
    // start sensor reading
    // response header
    cl.println("HTTP/1.1 200 OK");
    cl.println("Content-Type: application/json");  // JSON response type
    cl.println("Connection: close");               // close connection after response
    cl.println();
    // open JSON
    cl.print("{");
    // temperature
    cl.print(",\"1_floor_temperature\":\"");
    cl.print(dht_first.readTemperature(),1);
    cl.print("\"");
    // humidity
    cl.print(",\"1_floor_humidity\":\"");
    cl.print(dht_first.readHumidity(),1);
    cl.print("\"");
    cl.print(",\"2_floor_temperature\":\"");
    cl.print(dht_second.readTemperature(),1);
    cl.print("\"");
    // humidity
    cl.print(",\"2_floor_humidity\":\"");
    cl.print(dht_second.readHumidity(),1);
    cl.print("\"");
    // close json
    cl.println("}");
    return;
  }

  data = form_branch_status_json();
  send_data_to_client(cl, host, data);
  return;
}

void send_data_to_client(EthernetClient client, String host, String data){
  // Send request
  Serial.println("Send data" + data);
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Host: " + host);
  client.println("Connection: close");
  client.print("Content-Length: ");
  client.println(data.length());
  client.println();
  client.print(data);
  Serial.println("done");
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

void branches_status(){
  branch_1_status = digitalRead(branch_1);
  branch_2_status = digitalRead(branch_2);
  branch_3_status = digitalRead(branch_3);
  branch_4_status = digitalRead(branch_4);
  branch_5_status = digitalRead(branch_5);
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

String form_branch_status_json(){
  //update branch status
  branches_status();
  String res = "{";
  res = res + "\"1\":"+"\""+String(branch_1_status)+"\", ";
  res = res + "\"2\":"+"\""+String(branch_2_status)+"\", ";
  res = res + "\"3\":"+"\""+String(branch_3_status)+"\", ";
  res = res + "\"4\":"+"\""+String(branch_4_status)+"\", ";
  res = res + "\"5\":"+"\""+String(branch_5_status)+"\"} ";

  return res;
}


String get_host_from_request(String request){
  return "192.168.1.143";
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





