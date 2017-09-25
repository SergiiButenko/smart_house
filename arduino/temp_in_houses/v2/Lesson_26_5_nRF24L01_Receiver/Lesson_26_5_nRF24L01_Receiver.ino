// Библиотека RF24 для работы с радио модулем nRF24L01+           http://iarduino.ru/file/27.html
// Библиотека iarduino_4LED для работы с LED индикатором          http://iarduino.ru/file/266.html
// Передача и приём данных осуществляется через nRF24L01+         http://iarduino.ru/shop/Expansion-payments/nrf24l01-wireless-module-2-4g.html
// Радио модуль подключается через адаптер                        http://iarduino.ru/shop/Expansion-payments/adapter-dlya-nrf24l01.html
// Управление сервоприводом                                       http://iarduino.ru/shop/Mehanika/servoprivody/ осуществляется поворотом Trema потенциометра http://iarduino.ru/shop/Expansion-payments/potenciometr-trema-modul.html
// Данные на Trema четырехразрядный LED индикатор                 http://iarduino.ru/shop/Displei/chetyrehrazryadnyy-indikator-led-trema-modul.html считываются с Trema слайдера http://iarduino.ru/shop/Expansion-payments/polzunok-slider.html
// Для удобства подключения воспользуйтесь Trema Shield           http://iarduino.ru/shop/Expansion-payments/trema-shield.html

#include <SPI.h>                                               // Подключаем библиотеку  для работы с шиной SPI
#include <nRF24L01.h>                                          // Подключаем файл настроек из библиотеки RF24
#include <RF24.h>                                              // Подключаем библиотеку  для работы с nRF24L01+
RF24           radio(7, 8);                                   // Создаём объект radio   для работы с библиотекой RF24, указывая номера выводов nRF24L01+ (CE, CSN)

int            data[1];                                        // Создаём массив         для приёма данных (так как мы будем принимать от каждого передатчика только одно двухбайтное число, то достаточно одного элемента массива типа int)
uint8_t        pipe;                                           // Создаём переменную     для хранения номера трубы, по которой пришли данные
// Для данного примера, можно использовать не массив data из одного элемента, а переменную data типа int
void setup(){
  delay(1000);
  Serial.begin(9600);
  radio.begin();                                             // Инициируем работу nRF24L01+
  radio.setChannel(5);                                       // Указываем канал приёма данных (от 0 до 127), 5 - значит приём данных осуществляется на частоте 2,405 ГГц (на одном канале может быть только 1 приёмник и до 6 передатчиков)
  radio.setDataRate     (RF24_250KBPS);                        // Указываем скорость передачи данных (RF24_250KBPS, RF24_1MBPS, RF24_2MBPS), RF24_1MBPS - 1Мбит/сек
  radio.setPALevel      (RF24_PA_HIGH);                      // Указываем мощность передатчика (RF24_PA_MIN=-18dBm, RF24_PA_LOW=-12dBm, RF24_PA_HIGH=-6dBm, RF24_PA_MAX=0dBm)
  radio.openReadingPipe (1, 0xAABBCCDD11LL);                 // Открываем 1 трубу с идентификатором 1 передатчика 0xAABBCCDD11, для приема данных
  radio.openReadingPipe (2, 0xAABBCCDD22LL);                 // Открываем 2 трубу с идентификатором 2 передатчика 0xAABBCCDD22, для приема данных
  radio.startListening  ();                                  // Включаем приемник, начинаем прослушивать открытые трубы
  //  radio.stopListening   ();                                  // Выключаем приёмник, если потребуется передать данные
}

void loop(){
  if(radio.available(&pipe)){                                // Если в буфере имеются принятые данные, то получаем номер трубы, по которой они пришли, по ссылке на переменную pipe
    radio.read(&data, sizeof(data));                       // Читаем данные в массив data и указываем сколько байт читать
    if(pipe==1){
      Serial.print("Temp ");
      Serial.println((data[0] - 1000)/100);

      Serial.print("hum ");
      Serial.println((data[1] - 1000)/100);

    } 
    if(pipe==2){
      Serial.println(data[0]);
    }                   // Если данные пришли от 2 передатчика, то выводим показания Trema слайдера на индикатор
  }
}

