import RPi.GPIO as GPIO
import asyncio
import time
import requests
import datetime


class PintuOtomatis:
    def __init__(self):
        # Pin konfigurasi detektor
        self.DETEKTOR_LUAR = 24  # sensor luar
        self.DETEKTOR_DALAM = 23  # sensor dalam

        # Motor Stepper pin
        self.out1 = 5
        self.out2 = 6
        self.out3 = 13
        self.out4 = 19

        # Relay pin untuk lampu (aktif low)
        self.RELAY_PIN = 17

        # Kecepatan motor
        self.rotation_speed = 3
        self.step_sleep = 1 / (50 * self.rotation_speed)

        # Status pintu dan jumlah orang
        self.door_open = False
        self.jumlah_orang = 0
        self.jeda = 3  # detik untuk timeout deteksi

        self.API_BASE_URL = "http://192.168.137.19:5000"  # Replace with your server IP if different
        self.PEOPLE_COUNT_ENDPOINT = f"{self.API_BASE_URL}/api/people"

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.DETEKTOR_LUAR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.DETEKTOR_DALAM, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.setup(self.out1, GPIO.OUT)
        GPIO.setup(self.out2, GPIO.OUT)
        GPIO.setup(self.out3, GPIO.OUT)
        GPIO.setup(self.out4, GPIO.OUT)

        GPIO.setup(self.RELAY_PIN, GPIO.OUT)
        GPIO.output(self.RELAY_PIN, GPIO.HIGH)  # relay mati awalnya (aktif low)

        self._reset_motor()
        self._update_relay()

    def _reset_motor(self):
        GPIO.output(self.out1, GPIO.LOW)
        GPIO.output(self.out2, GPIO.LOW)
        GPIO.output(self.out3, GPIO.LOW)
        GPIO.output(self.out4, GPIO.LOW)

    def _update_relay(self):
        # Hidupkan lampu jika ada orang >=1, matikan jika 0
        if self.jumlah_orang >= 1:
            GPIO.output(self.RELAY_PIN, GPIO.LOW)  # Relay aktif (ON)
        else:
            GPIO.output(self.RELAY_PIN, GPIO.HIGH)  # Relay mati (OFF)

    def kirim_orang(self, count):
        payload = {
            "jumlah_orang": count
        }

        try:
            response = requests.post(self.PEOPLE_COUNT_ENDPOINT, json=payload)
            if response.status_code == 201:
                print(f"[{datetime.now()}] Successfully posted people count: {count}")
            else:
                print(f"[{datetime.now()}] Error posting data. Status code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Connection error: {str(e)}")

    async def buka_pintu(self):
        if not self.door_open:
            print("Membuka pintu...")
            for i in range(500, 0, -1):
                self._putar_motor(i)
                await asyncio.sleep(self.step_sleep)
            self.door_open = True

    async def tutup_pintu(self):
        if self.door_open:
            print("Menutup pintu...")
            for i in range(500):
                self._putar_motor(i)
                await asyncio.sleep(self.step_sleep)
            self.door_open = False

    def _putar_motor(self, i):
        step = i % 4
        GPIO.output(self.out4, GPIO.HIGH if step == 0 else GPIO.LOW)
        GPIO.output(self.out3, GPIO.HIGH if step == 2 else GPIO.LOW)
        GPIO.output(self.out2, GPIO.HIGH if step == 1 else GPIO.LOW)
        GPIO.output(self.out1, GPIO.HIGH if step == 3 else GPIO.LOW)

    async def deteksi_orang(self):
        print("Sistem detektor aktif.")
        while True:
            # Deteksi MASUK
            if GPIO.input(self.DETEKTOR_LUAR):
                print("Ada orang dari luar...")
                await self.buka_pintu()
                while GPIO.input(self.DETEKTOR_LUAR):
                    await asyncio.sleep(0.1)
                timeout_start = time.time()
                while time.time() - timeout_start < 5:
                    if GPIO.input(self.DETEKTOR_DALAM):
                        await self.tutup_pintu()
                        self.jumlah_orang += 1
                        print("Orang sudah masuk")
                        print(f"Jumlah orang sekarang: {self.jumlah_orang}")
                        self.kirim_orang(self.jumlah_orang)
                        self._update_relay()
                        break
                    await asyncio.sleep(0.1)
                else:
                    await self.tutup_pintu()
                    print("Orang ga jadi masuk, pintu nutup otomatis")
                await asyncio.sleep(5)  # delay siklus

            # Deteksi KELUAR
            if GPIO.input(self.DETEKTOR_DALAM):
                print("Ada orang dari dalam...")
                await self.buka_pintu()
                while GPIO.input(self.DETEKTOR_DALAM):
                    await asyncio.sleep(0.1)
                timeout_start = time.time()
                while time.time() - timeout_start < 5:
                    if GPIO.input(self.DETEKTOR_LUAR):
                        await self.tutup_pintu()
                        if self.jumlah_orang > 0:
                            self.jumlah_orang -= 1
                        print("Orang sudah keluar")
                        print(f"Jumlah orang sekarang: {self.jumlah_orang}")
                        self._update_relay()
                        break
                    await asyncio.sleep(0.1)
                else:
                    await self.tutup_pintu()
                    print("Orang ga jadi keluar, pintu nutup otomatis")
                await asyncio.sleep(5)  # delay siklus

            await asyncio.sleep(0.1)

    def run(self):
        try:
            asyncio.run(self.deteksi_orang())
        except KeyboardInterrupt:
            print("\nProgram dihentikan.")
            GPIO.cleanup()
