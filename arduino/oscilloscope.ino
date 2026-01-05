#include <TimerOne.h>
#include <math.h>

#define INPUT_PIN A0
#define OUTPUT_PIN 9
#define BUFFER_SIZE 64

const int samplePeriod = 100; //microseconds (10kHz)

volatile uint16_t buffer[BUFFER_SIZE];
volatile uint8_t head = 0;
volatile uint8_t tail = 0;
volatile uint32_t droppedSamples = 0;

const float frequency = 30.0;  // Hz
const int amplitude = 127;     // PWM amplitude
const int offset = 128;        // PWM midpoint

const float sampleRate = 1000000.0 / samplePeriod; // 0kHz
volatile float phase = 0.0;
volatile float phaseIncrement;

void recordVoltage();

void setup()
{
  pinMode(INPUT_PIN, INPUT);
  pinMode(OUTPUT_PIN, OUTPUT);

  phaseIncrement = 2.0 * PI * frequency / sampleRate;

  //initialize TimerOne interrupts every sample period to record voltage
  Timer1.initialize(samplePeriod);
  Timer1.attachInterrupt(recordVoltage);
  
  Serial.begin(115200);
}

void loop() {
unsigned long now = micros();

  //sine wave output 
  phase += phaseIncrement;
  if (phase >= 2.0 * PI) phase -= 2.0 * PI;

  int value = offset + amplitude * sin(phase);
  analogWrite(OUTPUT_PIN, value);
  
  //send a sample if a new sample is available
  if(head != tail) {
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