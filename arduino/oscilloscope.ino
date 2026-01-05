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

const float frequency = 120.0;  // Hz
const int amplitude = 127;     // PWM amplitude
const int offset = 128;        // PWM midpoint
const int samplesPerCycle = 128; // higher resolution for smoother sine wave

unsigned long lastUpdate = 0;
int sampleIndex = 0;
unsigned long sampleInterval;    //microseconds for each sample

void recordVoltage();

void setup()
{
  pinMode(INPUT_PIN, INPUT);
  pinMode(OUTPUT_PIN, OUTPUT);

  sampleInterval = 1000000UL / (frequency * samplesPerCycle); // microseconds

  //initialize TimerOne interrupts every sample period to record voltage
  Timer1.initialize(samplePeriod);
  Timer1.attachInterrupt(recordVoltage);
  
  Serial.begin(115200);
}

void loop() {
unsigned long now = micros();

  //Sine wave output
  if (now - lastUpdate >= sampleInterval) {
    lastUpdate += sampleInterval;

    float angle = 2.0 * PI * sampleIndex / samplesPerCycle;
    int value = offset + amplitude * sin(angle);
    analogWrite(OUTPUT_PIN, value);

    sampleIndex++;
    if (sampleIndex >= samplesPerCycle) sampleIndex = 0;
  }
  
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