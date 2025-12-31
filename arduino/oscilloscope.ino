#define INPUT_PIN A0

//const int R1 = 10000;
//const int R2 = 10000;

const int samplePeriod = 100; //microseconds (10kHz)

void setup()
{
  pinMode(INPUT_PIN, INPUT);
  Serial.begin(115200);
}

void loop()
{
  unsigned long now = micros();
  static unsigned long lastSample = 0;
  
  //timing
  if (now - lastSample < samplePeriod){ return; }
  else { lastSample = now; }
  
  //determine voltage over connection
  int pinVal = analogRead(INPUT_PIN);
  //float sensorVoltage = pinVal * 5.0 / 1023.0;
  //float voltage = sensorVoltage * (R1 + R2) / R2;
  
  //plot to serial monitor
  Serial.println(pinVal);
}