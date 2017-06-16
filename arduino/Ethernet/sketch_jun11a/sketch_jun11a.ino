//use ' instead of " in the html 
//address will look like http://192.168.1.102:84 when submited
//for use with W5100 based ethernet shields
///note that the below bug fix may be required
// http://code.google.com/p/arduino/issues/detail?id=605 

#include <SPI.h>
#include <Ethernet.h>

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED }; //physical mac address
byte ip[] = { 192, 168, 1, 102 }; // ip in lan
byte gateway[] = { 192, 168, 1, 1 }; // internet access via router
byte subnet[] = { 255, 255, 255, 0 }; //subnet mask
EthernetServer server(84); //server port

String readString; 

//////////////////////

void setup(){

  pinMode(5, OUTPUT); //pin selected to control
  pinMode(6, OUTPUT); //pin selected to control
  pinMode(7, OUTPUT); //pin selected to control
  pinMode(8, OUTPUT); //pin selected to control
  //start Ethernet
  Ethernet.begin(mac, ip, gateway, gateway, subnet);
  server.begin();

  //enable serial data print 
  Serial.begin(9600); 
  Serial.println("server multi pin button test 1.0"); // so I can keep track of what is loaded
}

void loop(){
  // Create a client connection
  EthernetClient client = server.available();
  if (client) {
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();

        //read char by char HTTP request
        if (readString.length() < 100) {

          //store characters to string 
          readString += c; 
          //Serial.print(c);
        } 

        //if HTTP request has ended
        if (c == '\n') {

          ///////////////
          Serial.println(readString); //print to serial monitor for debuging 

          client.println("HTTP/1.1 200 OK"); //send new page
          client.println("Content-Type: text/html");
          client.println();

          client.println("<HTML>");
          client.println("<HEAD>");
          client.println("<TITLE>Arduino GET test page</TITLE>");
          client.println("</HEAD>");
          client.println("<BODY>");

          client.println("<H1>Zoomkat's simple Arduino button</H1>");
          
          // For simple testing, pin 5, 6, 7, and 8 are used in buttons
          // DIY buttons
          client.println("<a href=/?on2 >5 ON</a>"); 
          client.println("<a href=/?off3 >5 OFF</a>"); 
          client.println("&nbsp;<a href=/?off357 >ALL OFF</a><br><br>"); 

          // mousedown buttons
          client.println("<input type=button value='6 ON' onmousedown=location.href='/?on4;'>"); 
          client.println("<input type=button value= '6 OFF' onmousedown=location.href='/?off5;'>");        
          client.println("&nbsp;<input type=button value='ALL OFF' onmousedown=location.href='/?off3579;'><br><br>");        
                   
          // mousedown radio buttons
          client.println("<input type=radio onmousedown=location.href='/?on6;'>7 ON</>"); 
          client.println("<input type=radio onmousedown=location.href='/?off7;'>7 OFF</>"); 
          client.println("&nbsp;<input type=radio onmousedown=location.href='/?off3579;'>ALL OFF</><br><br>");    
   
          
          // custom buttons
          client.print("<input type=submit value='8 ON' style=width:100px;height:45px onClick=location.href='/?on8;'>");
          client.print("<input type=submit value='8 OFF' style=width:100px;height:45px onClick=location.href='/?off9;'>");
          client.print("&nbsp;<input type=submit value='ALL OFF' style=width:100px;height:45px onClick=location.href='/?off3579;'>");

          client.println("</BODY>");
          client.println("</HTML>");

          delay(1);
          //stopping client
          client.stop();

          ///////////////////// control arduino pin
          if(readString.indexOf('2') >0)//checks for 2
          {
            digitalWrite(5, HIGH);    // set pin 5 high
            Serial.println("Led 5 On");
          }
          if(readString.indexOf('3') >0)//checks for 3
          {
            digitalWrite(5, LOW);    // set pin 5 low
            Serial.println("Led 5 Off");
          }
          
          if(readString.indexOf('4') >0)//checks for 4
          {
            digitalWrite(6, HIGH);    // set pin 6 high
            Serial.println("Led 6 On");
          }
          if(readString.indexOf('5') >0)//checks for 5
          {
            digitalWrite(6, LOW);    // set pin 6 low
            Serial.println("Led 6 Off");
          }
          
           if(readString.indexOf('6') >0)//checks for 6
          {
            digitalWrite(7, HIGH);    // set pin 7 high
            Serial.println("Led 7 On");
          }
          if(readString.indexOf('7') >0)//checks for 7
          {
            digitalWrite(7, LOW);    // set pin 7 low
            Serial.println("Led 7 Off");
          }     
          
            if(readString.indexOf('8') >0)//checks for 8
          {
            digitalWrite(8, HIGH);    // set pin 8 high
            Serial.println("Led 8 On");
          }
          if(readString.indexOf('9') >0)//checks for 9
          {
            digitalWrite(8, LOW);    // set pin 8 low
            Serial.println("Led 8 Off");
          }         
             
          //clearing string for next read
          readString="";

        }
      }
    }
  }
} 
