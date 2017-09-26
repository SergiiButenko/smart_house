// Библиотека RF24 для работы с радио модулем nRF24L01+           http://iarduino.ru/file/27.html
// Библиотека iarduino_4LED для работы с LED индикатором          http://iarduino.ru/file/266.html
// Передача и приём данных осуществляется через nRF24L01+         http://iarduino.ru/shop/Expansion-payments/nrf24l01-wireless-module-2-4g.html
// Радио модуль подключается через адаптер                        http://iarduino.ru/shop/Expansion-payments/adapter-dlya-nrf24l01.html
// Управление сервоприводом                                       http://iarduino.ru/shop/Mehanika/servoprivody/ осуществляется поворотом Trema потенциометра http://iarduino.ru/shop/Expansion-payments/potenciometr-trema-modul.html
// Данные на Trema четырехразрядный LED индикатор                 http://iarduino.ru/shop/Displei/chetyrehrazryadnyy-indikator-led-trema-modul.html считываются с Trema слайдера http://iarduino.ru/shop/Expansion-payments/polzunok-slider.html
// Для удобства подключения воспользуйтесь Trema Shield           http://iarduino.ru/shop/Expansion-payments/trema-shield.html

#include <SPI.h>                                               // Подключаем библиотеку для работы с шиной SPI
#include <nRF24L01.h>                                          // Подключаем файл настроек из библиотеки RF24
#include <RF24.h>                                              // Подключаем библиотеку для работы с nRF24L01+
RF24           radio(9, 10);                                   // Создаём объект radio для работы с библиотекой RF24, указывая номера выводов nRF24L01+ (CE, CSN)
int            data[1];                                        // Создаём массив для передачи данных (так как мы будем передавать только одно двухбайтное число, то достаточно одного элемента массива типа int)
                                                               // Для данного примера, можно использовать не массив data из одного элемента, а переменную data типа int
void setup(){
    radio.begin();                                             // Инициируем работу nRF24L01+
    radio.setChannel(5);                                       // Указываем канал передачи данных (от 0 до 127), 5 - значит передача данных осуществляется на частоте 2,405 ГГц (на одном канале может быть только 1 приёмник и до 6 передатчиков)
    radio.setDataRate     (RF24_1MBPS);                        // Указываем скорость передачи данных (RF24_250KBPS, RF24_1MBPS, RF24_2MBPS), RF24_1MBPS - 1Мбит/сек
    radio.setPALevel      (RF24_PA_HIGH);                      // Указываем мощность передатчика (RF24_PA_MIN=-18dBm, RF24_PA_LOW=-12dBm, RF24_PA_HIGH=-6dBm, RF24_PA_MAX=0dBm)
    radio.openWritingPipe (0xAABBCCDD11LL);                    // Открываем трубу с идентификатором 0xAABBCCDD11 для передачи данных (на ожном канале может быть открыто до 6 разных труб, которые должны отличаться только последним байтом идентификатора)
}

void loop(){
    data[0] = analogRead(A0);                                  // считываем значение с аналогового входа A0
    radio.write(&data, sizeof(data));                          // отправляем данные из массива data указывая сколько байт массива мы хотим отправить
    delay(50);                                                 // устанавливаем задержку на 50 мс, за это время приемник успеет принять и обработать данные этого и другого передатчика.
}
