from machine import Pin, PWM
from umqtt.simple import MQTTClient
import network
import ujson
import time


class Lancha(object):
    DIR_MIN = 25
    DIR_MAX = 125
    DIR_CENTER = 75

    def __init__(self):
        self.wifi = None
        self.mqtt = None
        self.config = ujson.load(open("settings.json"))
        self.motor = Pin(4, Pin.OUT)
        self.servo = PWM(Pin(5),freq=50)
        self.current_dir = Lancha.DIR_CENTER

        # duty for servo is between 40 - 115
        # servo.duty(100)
    
    def wifi_connect(self):
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi.active(True)
        if not self.wifi.isconnected():
            print("connect to {} {}".format(self.config["wifi"]["ssid"], self.config["wifi"]["pass"]))
            self.wifi.connect(self.config["wifi"]["ssid"], self.config["wifi"]["pass"])
        while not self.wifi.isconnected():
            print("waiting for internet")
            time.sleep(1)
        return self.wifi.isconnected()
    
    def mqtt_connect(self):
        cfg = self.config["mqtt"]
        self.mqtt = MQTTClient(cfg["client_id"], 
                               cfg["host"],
                               port=cfg["port"],
                               user=cfg["user"],
                               password=cfg["pass"])
        
        self.mqtt.set_callback(self.message_received)

        status = self.mqtt.connect()
        if status == 0:
            return True
        return False

    def mqtt_subscribe(self):
        cfg = self.config["mqtt"]
        self.mqtt.subscribe(cfg["topic"])

    def message_received(self, topic, msg):
        print("{}--> {}".format(topic, msg))
        
        payload = ujson.loads(msg)
        if payload.get("type") == "motor":
            val = payload.get("value")
            if val == 1:
                self.motor.on()
            else:
                self.motor.off()        
        elif payload.get("type") == "direction":
            val = payload.get("value")
            if val == -1:
                self.set_left()
            elif val == 1:
                self.set_right()
            elif val == 0:
                self.set_center()

    def set_center(self):
        self.servo.duty(Lancha.DIR_CENTER)

    def set_left(self):
        self.servo.duty(Lancha.DIR_MIN)

    def set_right(self):
        self.servo.duty(Lancha.DIR_MAX)

    def run(self):
        # Blocking wait for message
        #self.mqtt.wait_msg()
        print("RUN!")
        while True:
            self.mqtt.check_msg()
            time.sleep(.1)

    
def main():
    lancha = Lancha()
    lancha.wifi_connect()
    lancha.mqtt_connect()
    lancha.mqtt_subscribe()
    lancha.run()


main()
