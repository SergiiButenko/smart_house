#include <SPI.h>                                               // Подключаем библиотеку для работы с шиной SPI
#include <nRF24L01.h>                                          // Подключаем файл настроек из библиотеки RF24
#include <RF24.h>                                              // Подключаем библиотеку для работы с nRF24L01+   
#include <DHT.h>;

RF24           radio(7, 8);  
// matrix with actual pin state + temp + hum
int            out_data[20];         
// matrix with expected pin state + start fingerprint
int            input_data[19];                                        // Создаём массив для передачи данных (так как мы будем передавать только одно двухбайтное число, то достаточно одного элемента массива типа int)
uint8_t        pipe;                                           // Создаём переменную     для хранения номера трубы, по которой пришли данные


#define DHTPIN 4     // what pin we're connected to
#define DHTTYPE DHT22   // DHT 22  (AM2302)
DHT dht(DHTPIN, DHTTYPE);

void setup(){
  delay(1000);
  Serial.begin(9600);
  radio.begin();                                             // Инициируем работу nRF24L01+
  radio.setChannel(5);                                       // Указываем канал приёма данных (от 0 до 127), 5 - значит приём данных осуществляется на частоте 2,405 ГГц (на одном канале может быть только 1 приёмник и до 6 передатчиков)
  radio.setDataRate     (RF24_250KBPS);                        // Указываем скорость передачи данных (RF24_250KBPS, RF24_1MBPS, RF24_2MBPS), RF24_1MBPS - 1Мбит/сек
  radio.setPALevel      (RF24_PA_MAX);                      // Указываем мощность передатчика (RF24_PA_MIN=-18dBm, RF24_PA_LOW=-12dBm, RF24_PA_HIGH=-6dBm, RF24_PA_MAX=0dBm)
  radio.openReadingPipe (1, 0xAABBCCDD11LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
  radio.startListening  ();                                  // Включаем приемник, начинаем прослушивать открытые трубы
}

boolean r = false;
boolean w = false;

void loop(){
  if(radio.available(&pipe)){                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
    radio.read(&input_data, sizeof(input_data));                       // Читаем данные в массив data и указываем сколько байт читать    
    if (input_data[19] == 1){
      w = true;     
      r = false;
    } 
    else if (input_data[19] == 2){
      r = true; 
      w = false;    
    } 
    else {
      // in case input_data[19] !== 1
      Serial.print("Responce won't be sent. Data reseived:");
      Serial.println(input_data);
      return;
    }

    delay(50);
    radio.stopListening();
    radio.openWritingPipe (0xAABBCCDD11LL);                    // Открываем трубу с идентификатором 0xAABBCCDD11 для передачи данных (на ожном канале может быть открыто до 6 разных труб, которые должны отличаться только последним байтом идентификатора)

    for (int j = 0; j < sizeof(input_data) - 1 ; j++) {
      if (w == true and input_data[j] != -1){
        digitalWrite(input_data[j]);
      }
      out_data[j] = digitalRead(j);
      Serial.println("pin: "+String(j) + " set to " + String(out_data[0]));
    }

    float hum = dht.readHumidity();
    float temp= dht.readTemperature(); 
    out_data[19] = temp*100 + 1000; 
    out_data[20] = hum*100 + 1000;

    for (int i = 0; i < 5; i++) { 
      if (radio.write(&out_data, sizeof(out_data))){                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
        Serial.println("data was sent");
        delay(1000);
        break;
      } 
      else {
        Serial.println("data wasn't sent");
      }
    }

    Serial.println(out_data);      
    radio.openReadingPipe (1, 0xAABBCCDD11LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
    radio.startListening  ();                                  // Включаем приемник, начинаем прослушивать открытые трубы
  }
}





