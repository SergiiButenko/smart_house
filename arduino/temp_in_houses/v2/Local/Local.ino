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
const byte local_branch_1_pin = 3;
const byte local_branch_2_pin = 4;
const byte local_branch_3_pin = 5;
//remote
const byte remote_branch_1_pin = 2;
const byte remote_branch_2_pin = 3;
const byte remote_branch_3_pin = 6;
//remote 2
const byte remote_branch_1_pin = 2;
const byte remote_branch_2_pin = 3;
const byte remote_branch_3_pin = 6;

//local
byte local_branches[] = {
  20,21,22};
const byte local_branch_1_id = local_branches[0];
const byte local_branch_2_id = local_branches[1];
const byte local_branch_3_id = local_branches[2];
//remote
byte remote_branches[] = {
  23,24,25};
const byte remote_branch_1_id = remote_branches[0];
const byte remote_branch_2_id = remote_branches[1];
const byte remote_branch_3_id = remote_branches[2];

byte remote_branches_2[] = {
  26,27,28};
const byte remote_branch_4_id = remote_branches[0];
const byte remote_branch_5_id = remote_branches[1];
const byte remote_branch_6_id = remote_branches[2];


// timers only for current board
const byte timers_count = 18;
unsigned long int timers[18];

RF24           radio(7, 8);                                   // Создаём объект radio   для работы с библиотекой RF24, указывая номера выводов nRF24L01+ (CE, CSN)

int            data[2];                                        // Создаём массив         для приёма данных (так как мы будем принимать от каждого передатчика только одно двухбайтное число, то достаточно одного элемента массива типа int)
uint8_t        pipe;                                           // Создаём переменную     для хранения номера трубы, по которой пришли данные

int            remote_data_1_in[19];
int            remote_data_1_out[20];
int            remote_data_2_in[19];
int            remote_data_2_out[19];    
//remote_data[19] == 1 - init radio response

//remote_data[0] == 0 - pin 1 off
//remote_data[0] == 1 - pin 1 on

//remote_data[1] == 0 - pin 2 off
//remote_data[1] == 1 - pin 2 on

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
  pinMode(local_branch_1_pin, OUTPUT);
  pinMode(local_branch_2_pin, OUTPUT);
  pinMode(local_branch_3_pin, OUTPUT);


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


    if (arr_contains(local_branches, branch_id)){
      branch_on(branch_id, alert_time);
      delay(1);
      send_data_to_client(cl, get_all_data());
    } 
    else if (arr_contains(remote_branches, branch_id)) {
      data = remote_branch_on(branch_id, alert_time);
      delay(1);
      send_data_to_client(cl, data);
    }

    return;
  }

  if (HTTP_req.indexOf("/branch_off") > -1) { 
    byte id_start = HTTP_req.indexOf("branch_id=");
    byte id_end = HTTP_req.indexOf(" HTTP/1.1");
    String id_str = HTTP_req.substring(id_start+10, id_end);
    byte branch_id=id_str.toInt();

    if (arr_contains(local_branches, branch_id)){
      branch_off(branch_id);
      delay(1);
      send_data_to_client(cl, get_all_data());
    } 
    else if (arr_contains(remote_branches, branch_id)) {
      data = remote_branch_off(branch_id);
      delay(1);
      send_data_to_client(cl, data);
    }

    return;
  }


  if (HTTP_req.indexOf("/data") > -1) { 
    send_data_to_client(cl, get_all_data());
    return;
  }

}

void remote_branch_on(byte branch_id, int alert_time){
  byte pin = get_remote_branch_pin(branch_id);
  if (pin==0){
    return false;
  }
  
  byte id = get_remote_branch_pin(branch_id);
  if (pin==0){
    return false;
  }
  
  

  Serial.println("get temperature from 1");
  radio.stopListening();
  remote_data_1_in[19] = 2;
  radio.openWritingPipe (0xAABBCCDD11LL);
  //radio.openWritingPipe (0xAABBCCDD22LL);
  for (int i = 0; i < 5; i++) { 
    if (radio.write(&remote_data_1_in, sizeof(remote_data_1_in))){                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
      delay(1000);
      Serial.println("OK");
      radio.openReadingPipe(1, 0xAABBCCDD11LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
      radio.startListening();                                  // Включаем приемник, начинаем прослушивать открытые трубы


      int interval = 10 * 1000;
      unsigned long start_time = millis();
      unsigned long now;
      boolean data_retrived;
      do{
        now  = millis();
        data_retrived = radio.available(&pipe);
        if(pipe == 1) {                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
          radio.read(&remote_data_1_out, sizeof(remote_data_1_out));                       // Читаем данные в массив data и указываем сколько байт читать

          Serial.print("Temp ");
          remote_data_1_out[19] = (remote_data_1_out[19]- 1000)/100;
          Serial.println(remote_data_1_out[19]);

          Serial.print("hum ");
          remote_data_1_out[20] = (remote_data_1_out[20]- 1000)/100;
          Serial.println(remote_data_1_out[20]);
          break;
        }
      }       
      while(now - start_time <= interval);

      if (data_retrived == true){
        break;
      } 
    }      

    Serial.println("Failed to get data from 1");
    delay(1000);

  }
}


byte get_remote_id(byte branch_id){
  if (arr_contains(remote_branched, branch_id)){
    return 1;
  }
  
  if (arr_contains(remote_branched_2, branch_id)){
    return 2;
  }
  
  return 0;
  
}

void branch_on(byte branch_id, int alert_time){
  byte pin = get_branch_pin(branch_id);
  if (pin==0){
    return;
  }

  on(pin, alert_time);
}

// turn on off logic
void on(byte pin, int alert_time){
  // Add timers rule
  timers[pin] = long(millis() / 60000 + alert_time);
  digitalWrite(pin,HIGH);
}

void branch_off(byte branch_id){
  byte pin = get_branch_pin(branch_id);
  if (pin==0){
    return;
  }

  off(pin);
}


void off(byte pin){
  // Remove timers rule
  timers[pin]=0;
  digitalWrite(pin,LOW);
}


byte get_branch_pin(byte branch_id){
  if (!arr_contains(local_branches, branch_id)){
    return 0;
  }

  if (branch_id==local_branch_1_id){
    return local_branch_1_pin;
  }

  if (branch_id==local_branch_2_id){
    return local_branch_2_pin;
  }

  if (branch_id==local_branch_3_id){
    return local_branch_3_pin;
  }

  return 0;
}


byte get_remote_branch_pin(byte branch_id){
  if (!arr_contains(remote_branches, branch_id)){
    return 0;
  }
  
  if (!arr_contains(remote_branches_2, branch_id)){
    return 0;
  }

  if (branch_id==remote_branch_1_id){
    return remote_branch_1_pin;
  }

  if (branch_id==remote_branch_2_id){
    return remote_branch_2_pin;
  }

  if (branch_id==remote_branch_3_id){
    return remote_branch_3_pin;
  }
  
  if (branch_id==remote_branch_4_id){
    return remote_branch_4_pin;
  }

  if (branch_id==remote_branch_5_id){
    return remote_branch_5_pin;
  }

  if (branch_id==remote_branch_6_id){
    return remote_branch_6_pin;
  }

  return 0;
}


void check_all_branches_timer(){
  for (byte i = 0; i < timers_count; i++) {
    if (timers[i]==0){
      continue;
    } 

    if ( int(timers[i] - millis() / 60000) < 0  ){        
      off(i); 
    }
  }
}

String get_all_data(){
  Serial.println("get temperature from 1");
  radio.stopListening();
  remote_data_1_in[19] = 2;
  radio.openWritingPipe (0xAABBCCDD11LL);
  //radio.openWritingPipe (0xAABBCCDD22LL);
  for (int i = 0; i < 5; i++) { 
    if (radio.write(&remote_data_1_in, sizeof(remote_data_1_in))){                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
      delay(1000);
      Serial.println("OK");
      radio.openReadingPipe(1, 0xAABBCCDD11LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
      radio.startListening();                                  // Включаем приемник, начинаем прослушивать открытые трубы


      int interval = 10 * 1000;
      unsigned long start_time = millis();
      unsigned long now;
      boolean data_retrived;
      do{
        now  = millis();
        data_retrived = radio.available(&pipe);
        if(pipe == 1) {                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
          radio.read(&remote_data_1_out, sizeof(remote_data_1_out));                       // Читаем данные в массив data и указываем сколько байт читать

          Serial.print("Temp ");
          remote_data_1_out[19] = (remote_data_1_out[19]- 1000)/100;
          Serial.println(remote_data_1_out[19]);

          Serial.print("hum ");
          remote_data_1_out[20] = (remote_data_1_out[20]- 1000)/100;
          Serial.println(remote_data_1_out[20]);
          break;
        }
      }       
      while(now - start_time <= interval);

      if (data_retrived == true){
        break;
      } 
    }      

    Serial.println("Failed to get data from 1");
    delay(1000);

  }

  Serial.println("get temperature from 2");
  radio.stopListening();
  remote_data_2_in[19] = 2;
  radio.openWritingPipe (0xAABBCCDD22LL);
  for (int i = 0; i < 5; i++) { 
    if (radio.write(&remote_data_2_in, sizeof(remote_data_2_in))){                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
      delay(1000);
      Serial.println("OK");
      radio.openReadingPipe(2, 0xAABBCCDD22LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
      radio.startListening();                                  // Включаем приемник, начинаем прослушивать открытые трубы


      int interval = 10 * 1000;
      unsigned long start_time = millis();
      unsigned long now;
      boolean data_retrived;
      do {
        now  = millis();
        data_retrived = radio.available(&pipe);
        if(pipe == 2) {                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
          radio.read(&remote_data_2_out, sizeof(remote_data_2_out));                       // Читаем данные в массив data и указываем сколько байт читать

          Serial.print("Temp ");
          remote_data_2_out[19] = (remote_data_2_out[19]- 1000)/100;
          Serial.println(remote_data_2_out[19]);

          Serial.print("hum ");
          remote_data_2_out[20] = (remote_data_2_out[20]- 1000)/100;
          Serial.println(remote_data_2_out[20]);
          break;
        }
      } 
      while(now - start_time <= interval);

      if (data_retrived == true){
        break;
      } 
    }      

    Serial.println("Failed to get data from 2");
    delay(1000);

  }


  String res = "{";
  res = res + "\"temperature_1\":" +"\""+String(remote_data_1_out[19])+"\", ";
  res = res + "\"temperature_2\":" +"\""+String(remote_data_2_out[19])+"\", ";
  res = res + "\"humidity_1\":"+"\""+String(remote_data_1_out[20])+"\", ";
  res = res + "\"humidity_2\":"+"\""+String(remote_data_2_out[20])+"\", ";

  for (int i = 0; i < sizeof(local_branches); i++){
    byte pin = get_branch_pin(local_branches[i]);
    res = res + String(local_branches[i]) + ": \"" + String(digitalRead(pin)) + "\", ";      
  }

  for (int i = 0; i < sizeof(remote_branches) - 1; i++){
    byte pin = get_remote_branch_pin(remote_branches[i]);
    res = res + String(remote_branches[i]) + ": \"" + String(digitalRead(pin)) + "\", ";      
  }

  res = res + String( remote_branches[sizeof(remote_branches)] ) + ": \"" + String( digitalRead( get_remote_branch_pin( remote_branches[sizeof(remote_branches)] ))) + "\"} ";

  Serial.println(res);
  return res;
}

boolean arr_contains(byte arr[], int element){
  for (int i =0; i< sizeof(arr); i++){
    if (element == arr[i]){
      return true;
    }
  }

  return false;
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



