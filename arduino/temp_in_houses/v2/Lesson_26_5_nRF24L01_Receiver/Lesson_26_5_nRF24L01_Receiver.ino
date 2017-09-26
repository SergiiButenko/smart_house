#include <SPI.h>                                               // Подключаем библиотеку  для работы с шиной SPI
#include <nRF24L01.h>                                          // Подключаем файл настроек из библиотеки RF24
#include <RF24.h>                                              // Подключаем библиотеку  для работы с nRF24L01+
#include <Ethernet.h>

byte mac[] = { 
  0x40, 0xA2, 0xDA, 0xFE, 0x0E, 0x90 };
IPAddress ip(192, 168, 1, 20);
EthernetServer server(80);  
EthernetClient client;

String HTTP_req;                                              // stores the HTTP request

//local
const byte branch_1_pin = 3;
const byte branch_2_pin = 4;
const byte branch_3_pin = 5;
//remote
//const byte branch_4_pin = 2;
//const byte branch_5_pin = 3;
//const byte branch_6_pin = 6;

//local
const byte branch_1_id = 20;
const byte branch_2_id = 21;
const byte branch_3_id = 22;
//remote
const byte branch_4_id = 23;
const byte branch_5_id = 24;
const byte branch_6_id = 25;

//local
byte branch_1_status=0;
byte branch_2_status=0;
byte branch_3_status=0;
//remote
byte branch_4_status=0;
byte branch_5_status=0;
byte branch_6_status=0;

// timers only for current board
const byte timers_count=5;
unsigned long int timers[timers_count];

RF24           radio(7, 8);                                   // Создаём объект radio   для работы с библиотекой RF24, указывая номера выводов nRF24L01+ (CE, CSN)

int            data[2];                                        // Создаём массив         для приёма данных (так как мы будем принимать от каждого передатчика только одно двухбайтное число, то достаточно одного элемента массива типа int)
uint8_t        pipe;                                           // Создаём переменную     для хранения номера трубы, по которой пришли данные

int            remote_data_downstares[6];    
int            remote_data_kids[6];    
//remote_data[0] == 1 - get temperature
//remote_data[0] == 2 - get branch statuses

//remote_data[1] == 0 - branch 4 off
//remote_data[1] == 1 - branch 4 on

//remote_data[2] == 0 - branch 5 off
//remote_data[2] == 1 - branch 5 on

//remote_data[3] == 0 - branch 6 off
//remote_data[3] == 1 - branch 6 on

//remote_data[4] == temp
//remote_data[5] == hum

void setup(){
  delay(1000);

  // Start Serial
  Serial.begin(115200);

  for (byte i = 0; i > timers_count; i++) {
    timers[i]=0;
  }

  // Init all outputs
  pinMode(branch_1_pin, OUTPUT);
  pinMode(branch_2_pin, OUTPUT);
  pinMode(branch_3_pin, OUTPUT);


  radio.begin();                                             // Инициируем работу nRF24L01+
  radio.setChannel(5);                                       // Указываем канал приёма данных (от 0 до 127), 5 - значит приём данных осуществляется на частоте 2,405 ГГц (на одном канале может быть только 1 приёмник и до 6 передатчиков)
  radio.setDataRate     (RF24_250KBPS);                        // Указываем скорость передачи данных (RF24_250KBPS, RF24_1MBPS, RF24_2MBPS), RF24_1MBPS - 1Мбит/сек
  radio.setPALevel      (RF24_PA_MAX);                      // Указываем мощность передатчика (RF24_PA_MIN=-18dBm, RF24_PA_LOW=-12dBm, RF24_PA_HIGH=-6dBm, RF24_PA_MAX=0dBm)

  //  Start the Ethernet connection and the server
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

void loop(){
  EthernetClient client = server.available();  // try to get client
  process_incoming_client(client);        
  check_all_branches_timer();
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
  String data="";

  if (HTTP_req.indexOf("/favicon.ico") > -1) { 
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
    send_data_to_client(cl, get_all_data());
    return;
  }

  if (HTTP_req.indexOf("/branch_off") > -1) { 
    byte id_start = HTTP_req.indexOf("branch_id=");
    byte id_end = HTTP_req.indexOf(" HTTP/1.1");
    String id_str = HTTP_req.substring(id_start+10, id_end);
    byte branch_id=id_str.toInt();

    off(branch_id);
    delay(1);
    send_data_to_client(cl, get_all_data());
    return;
  }


  if (HTTP_req.indexOf("/data") > -1) { 
    send_data_to_client(cl, get_all_data());
    return;
  }

}

void send_data_to_client(EthernetClient client, String data){
  // Send request
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Host: 192.168.1.143");
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


byte get_branch_pin(byte i){
  if (i==branch_1_id){
    return branch_1_pin;
  }
  if (i==branch_2_id){
    return branch_2_pin;
  }
  if (i==branch_3_id){
    return branch_3_pin;
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

String get_all_data(){
  Serial.println("get temperature from 1rst flor");
    radio.stopListening();
    remote_data_downstares[0] = 1;
    radio.openWritingPipe (0xAABBCCDD11LL);
    //radio.openWritingPipe (0xAABBCCDD22LL);
    for (int i = 0; i < 5; i++) { 
      if (radio.write(&remote_data_downstares, sizeof(remote_data_downstares))){                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
        delay(1000);
        Serial.println("OK");
        radio.openReadingPipe (1, 0xAABBCCDD11LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
        radio.startListening  ();                                  // Включаем приемник, начинаем прослушивать открытые трубы

        while(1){
          if (radio.available(&pipe)){                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
            radio.read(&remote_data_downstares, sizeof(remote_data_downstares));                       // Читаем данные в массив data и указываем сколько байт читать

            Serial.print("Temp ");
            remote_data_downstares[4] = (remote_data_downstares[4]- 1000)/100;
            Serial.println(remote_data_downstares[4]);

            Serial.print("hum ");
            remote_data_downstares[5] = (remote_data_downstares[5]- 1000)/100;
            Serial.println(remote_data_downstares[5]);
            break;
          }
        } 
      }      
      else {
        Serial.println("Failed to get data from 1rst flor");
        delay(1000);
      }
    }

    Serial.println("get temperature from kids room");
    radio.stopListening();
    remote_data_kids[0] = 1;
    radio.openWritingPipe (0xAABBCCDD22LL);
    for (int i = 0; i < 5; i++) { 
      if (radio.write(&remote_data_kids, sizeof(remote_data_kids))){                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
        delay(1000);
        Serial.println("OK");
        radio.openReadingPipe (2, 0xAABBCCDD22LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
        radio.startListening  ();                                  // Включаем приемник, начинаем прослушивать открытые трубы

        while(1){
          if (radio.available(&pipe)){                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
            radio.read(&remote_data_kids, sizeof(remote_data_kids));                       // Читаем данные в массив data и указываем сколько байт читать

            Serial.print("Temp ");
            remote_data_kids[4] = (remote_data_kids[4]- 1000)/100;
            Serial.println(remote_data_kids[4]);

            Serial.print("hum ");
            remote_data_kids[5] = (remote_data_kids[5]- 1000)/100;
            Serial.println(remote_data_kids[5]);
            break;
          }
        } 
      }      
      else {
        Serial.println("Failed to get data from kids room");
        delay(1000);
      }
    }

    String res = "{";
    res = res + "\"temperature_kids\":" +"\""+String(remote_data_kids[4])+"\", ";
    res = res + "\"temperature_downstares\":" +"\""+String(remote_data_downstares[4])+"\", ";
    res = res + "\"humidity_kids\":"+"\""+String(remote_data_kids[5])+"\", ";
    res = res + "\"humidity_downstares\":"+"\""+String(remote_data_downstares[5])+"\", ";
    res = res + "20:"+"\""+String(digitalRead(branch_1_pin))+"\", ";
    res = res + "21:"+"\""+String(digitalRead(branch_2_pin))+"\", ";
    res = res + "22:"+"\""+String(digitalRead(branch_3_pin))+"\", ";
    res = res + "23:"+"\""+String(remote_data_kids[1])+"\", ";
    res = res + "24:"+"\""+String(remote_data_kids[2])+"\", ";
    res = res + "25:"+"\""+String(remote_data_kids[3])+"\", ";
    res = res + "26:"+"\""+String(remote_data_downstares[1])+"\", ";
    res = res + "27:"+"\""+String(remote_data_downstares[2])+"\", ";
    res = res + "28:"+"\""+String(remote_data_downstares[3])+"\"}";
    Serial.println(res);
    return res;
}









