#include <SPI.h>
#include <Ethernet.h>


byte mac[] = { 0x90, 0xA2, 0xDA, 0x0E, 0xFE, 0x40 };
IPAddress ip(192, 168, 1, 10);
EthernetServer server(80);  

String HTTP_req;          // stores the HTTP request

int branch_1 = 2;
int branch_2 = 3;
int branch_3 = 4;
int branch_4 = 5;
int branch_5 = 6;
int branch_6 = 7;
int branch_7 = 8;
int pump = 9;

int branch_1_status=0;
int branch_2_status=0;
int branch_3_status=0;
int branch_4_status=0;
int branch_5_status=0;
int branch_6_status=0;
int branch_7_status=0;
int pump_status=0;

void setup()
{
// Start Serial
Serial.begin(115200);

// Init all outputs
pinMode(branch_1, OUTPUT);
pinMode(branch_2, OUTPUT);
inMode(branch_3, OUTPUT);
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
} else {
    server.begin();
    Serial.print("server is at ");
    Serial.println(Ethernet.localIP());
}


void loop()
{
    EthernetClient client = server.available();  // try to get client

    if (client) {  // got client?
        boolean currentLineIsBlank = true;
        while (client.connected()) {
            if (client.available()) {   // client data available to read
                char c = client.read(); // read 1 byte (character) from client
                HTTP_req += c;  // save the HTTP request 1 char at a time
                // last line of client request is blank and ends with \n
                // respond to client only after last line received
                if (c == '\n' && currentLineIsBlank) {
                    // send a standard http response header
                    client.println(http_headers());
                    
                    // Send request
                    data = form_branch_status_json();
                    client.println("POST /1/events HTTP/1.1");
                    client.println("Host: " + String(remote_server) + ":" + String(port));
                    client.println("Content-Type: application/x-www-form-urlencoded");
                    client.print("Content-Length: ");
                    client.println(data.length());
                    client.println();
                    client.print(data);

                    Serial.print(HTTP_req);
                    HTTP_req = "";    // finished with request, empty string
                    break;
                }
                // every line of text received from the client ends with \r\n
                if (c == '\n') {
                    // last character on line of received text
                    // starting new line with next character read
                    currentLineIsBlank = true;
                } 
                else if (c != '\r') {
                    // a text character was received from client
                    currentLineIsBlank = false;
                }
            } // end if (client.available())
        } // end while (client.connected())
        delay(1);      // give the web browser time to receive the data
        client.stop(); // close the connection
    } // end if (client)
}


// switch LED and send back HTML for LED checkbox
void ProcessCheckbox(EthernetClient cl)
{
    if (HTTP_req.indexOf("LED2=2") > -1) {  // see if checkbox was clicked
        // the checkbox was clicked, toggle the LED
        if (LED_status) {
            LED_status = 0;
        }
        else {
            LED_status = 1;
        }
    }
    
    if (LED_status) {    // switch LED on
        digitalWrite(2, HIGH);
        // checkbox is checked
        cl.println("<input type=\"checkbox\" name=\"LED2\" value=\"2\" \
        onclick=\"submit();\" checked>LED2");
    }
    else {              // switch LED off
        digitalWrite(2, LOW);
        // checkbox is unchecked
        cl.println("<input type=\"checkbox\" name=\"LED2\" value=\"2\" \
        onclick=\"submit();\">LED2");
    }
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
  if (branch_1_status==LOW and branch_2_status==LOW and branch_3_status==LOW and branch_4_status==LOW and branch_5_status==LOW
    and branch_5_status==LOW and branch_7_status==LOW){
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

void on(String branch){
  // Get state from command
  int pin = get_branch_pin(branch.toInt());
  
  digitalWrite(pin,HIGH);
  digitalWrite(pump, HIGH);

  branches_status();
}

void off(String branch){
  // Get state from command
  int pin = get_branch_pin(branch.toInt());

  digitalWrite(pin,LOW);
  branches_status();
  
  if ( if_no_branch_active() ){
    digitalWrite(pump, LOW);
  }

  branches_status();
}

String http_headers(){
  return "HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: POST, GET, PUT, OPTIONS\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n";
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

    return res
}



