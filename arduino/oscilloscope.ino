#include <TimerOne.h>

#define INPUT_PIN A0
#define BUFFER_SIZE 64

const int samplePeriod = 100; //microseconds (10kHz)

volatile int uint16_t buffer[BUFFER_SIZE];
volatile uint8_t head = 0;
volatile uint8_t tail = 0;
volatile uint32_t droppedSamples = 0;

void recordVoltage();

void setup()
{
  pinMode(INPUT_PIN, INPUT);

  //initialize TimerOne interrupts every sample period to record voltage
  Timer1.initialize(samplePeriod);
  Timer1.attachInterrupt(recordVoltage);
  
  Serial.begin(115200);
}

void loop() {
  //send a sample if a new sample is available
  while(head != tail) {
    noInterrupts();
    uint16_t sample = buffer[tail];
    tail = (tail + 1) & (BUFFER_SIZE - 1); //optimized % operator
    interrupts();

    Serial.println(sample);
  }
}

void recordVoltage() {
  uint8_t nextHead = (head + 1) & (BUFFER_SIZE - 1); //optimized % operator

  if (nextHead == tail) {
    droppedSamples++; //buffer is full therefore a sample is lost
  } else {
    buffer[head] = analogRead(INPUT_PIN);
    head = nextHead;
  }
}