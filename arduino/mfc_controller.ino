#define PID_INTEGER
#include "GyverPID.h"

int maxpwm = 1023;  //максимальное значение ШИМ, управляющего пропорциональным клапаном
int dt = 50;        //ms, интервал времени опроса расходомера

int valve = 0;      //ШИМ, подающийся на клапан
int realflow = 0;   //значение расхода, считываемое с расходомера
int targetflow = 0; //желаемое значение расхода в случае использования ПИД-регулятора

boolean pidon = 0;  //вкл/выкл ПИД-регулятор
float dtpid = 100;  //ms, интервал времени включения ПИД-регулятора
float Kp = 0.17;//0.1;//0.15;//0.2;     //коэффициент пропорциональной составляющей ПИД-регулятора
float Ki = 0.1;//0.01;//0.07;//0.3;       //интегральной
float Kd = 0.0;//0.0;//0.0005;       //дифференциальной
int minerr = 2;     // не включать ПИД-регулятор если ошибка меньше чем minerr. если minerr=0 будет всегда включаться

unsigned long last_time = 0;
unsigned long pid_last_time = 0;
int serialinp = 0;  //то, что считано с последовательного порта

int valve_pin = 9;//6; //пин к которому подключен пропорциональный клапан
int fm_pin = 14;       //пин к котором подключен расходомер

GyverPID pid(Kp, Ki, Kd); //класс ПИД-регулятора

void setup() {
  // Пины D9 и D10 - 7.8 кГц 10bit
  TCCR1A = 0b00000011; // 10bit
  TCCR1B = 0b00000001; // x1 phase correct

  pid.setLimits(0, maxpwm);
  pid.setIConstrain(-700, 700); //включение ограничения интегрального члена ПИД-регулятора

  pinMode(valve_pin, OUTPUT);
  pinMode(fm_pin, INPUT);

  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0)
  {
    serialinp = Serial.parseInt();
    Serial.read();
    //Serial.print("read: ");
    //Serial.println(serialinp);

    if (serialinp >= 0 && serialinp <= maxpwm)
    {
      pidon = 0;      //если полученное с порта число положительное и в интервале ШИМ, отключаем ПИД-регулятор и открываем клапан
      valve = serialinp;
      analogWrite(valve_pin, valve);
    }
    if (serialinp < 0 && serialinp >= -maxpwm)
    {
      pidon = 1;      //если полученное с порта число отрицательное включаем ПИД-регулятор с соответствующей целью
      targetflow = -serialinp;
      realflow = analogRead(fm_pin);
      pid.input = realflow;
      pid.setpoint = targetflow;
      pid.output = valve;
    }

  }

  if (pidon && millis() - pid_last_time >= dtpid)
  {
    pid_last_time = millis();   //если ПИД-регулятор включен и пришло время - считываем поток и задействуем регулятор

    realflow = analogRead(fm_pin);
    if (abs(realflow - targetflow) > minerr) //ПИД-регулятор включается только если ошибка больше минимально допустимой
    {
      pid.input = realflow;
      valve = pid.getResult();
      analogWrite(valve_pin, valve);
    }

    //Serial.print("pid output ");
    //Serial.println(pid.output);

  }

  if (millis() - last_time >= dt)
  {
    last_time = millis();       //с заданным интервалом опрашиваем расходомер и выводим значение в порт
    realflow = analogRead(fm_pin);
    Serial.print(realflow);   // В этой версии помимо значения расхода через запятую выводится величина открытия клапана
    Serial.print(",");
    Serial.println(valve);
  }
}
