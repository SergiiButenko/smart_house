#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <DHT.h>;

#define DHTPIN 4     // what pin we're connected to
#define DHTTYPE DHT22   // DHT 22  (AM2302)
DHT dht(DHTPIN, DHTTYPE);

RF24 radio(7, 8);

const byte rxAddr[6] = "00001";
//Variables
int chk;
float hum;  //Stores humidity value
float temp; //Stores temperature value

void setup()
{ 
  Serial.begin(9600);
  Serial.println("Start");
  radio.begin();
  radio.setRetries(15, 15);
  radio.openWritingPipe(rxAddr);
  
  radio.stopListening();
  dht.begin();
}

void loop()
{  
  float hum = dht.readHumidity();
  float temp= dht.readTemperature();  
  
  char humidity[8];
  dtostrf(hum, 6, 2, humidity);
  Serial.print("Hum ");
  Serial.println(humidity);
  
  char temperature[8];
  dtostrf(temp, 6, 2, temperature);
  Serial.print("Temp ");
  Serial.println(temperature);
 
  
  char text[17] = "1";

  strcat(text, humidity);
  strcat(text, temperature);

  radio.write(&text, sizeof(text));
  Serial.println(text);
  delay(5000);
}
