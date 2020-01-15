/*
 * ARTOPS: a Blackjack playing robot
 * Created by Oliver Colebourne & Patrick McGuckian
 * 11.12.2019
 */



#include <SparkFun_TB6612.h>
//motor control code sourced from adafruit website

#include <Adafruit_CircuitPlayground.h>

// these constants are used to allow you to make your motor configuration 
// line up with function names like forward.  Value can be 1 or -1
const int offsetA = 1;
const int offsetB = 1;
// Pins for all inputs, keep in mind the PWM defines must be on PWM pins
#define AIN1 A7
#define AIN2 A6
#define PWMA 9
#define STBY A1
#define BIN1 A4
#define BIN2 A5
#define PWMB 10


// put your setup code here, to run once:
// Initializing motors.  The library will allow you to initialize as many
// motors as you have memory for.  If you are using functions like forward
// that take 2 motors as arguements you can either write new functions or
// call the function more than once.
Motor motor1 = Motor(AIN1, AIN2, PWMA, offsetA, STBY); //top
Motor motor2 = Motor(BIN1, BIN2, PWMB, offsetB, STBY); //bottom



int run = 1;

void setup() {
Serial.begin(9600);
}

void loop()
{


if(Serial.available()) { //if serial message recieved then run shufflecards function.
     Serial.read();
     shuffleCards();
     Serial.flush();


}
delay(1000);
}

void shuffleCards(){

for (int i=0; i<10; i++){
        int randmotor = random(0,2);
        if (randmotor == 1){ 
          motor1.drive(250,125);
          delay(50);
          motor1.drive(-200,100);
          motor1.brake();
          delay(10);
        }
        else if (randmotor == 0){
          motor2.drive(220,125);
          delay(50);
          motor2.drive(-125,75);
          motor2.brake();
          delay(10);
        }
        
      }
      forward(motor1, motor2, 255); //run both motors at the end to ensure good shuffle
        delay(1000);
        brake(motor1, motor2);
  Serial.println("complete"); //send message back to RPi
}
