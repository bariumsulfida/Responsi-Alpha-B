import smbus2
import time

class MPU6050:
    def __init__(self, bus_number=1, device_address=0x68):
        """Inisialisasi sensor MPU6050."""
        self.device_address = device_address
        self.bus = smbus2.SMBus(bus_number)  # Inisialisasi I2C bus
        self.offset_x = self.offset_y = self.offset_z = 0
        self._init_sensor()

    def _init_sensor(self):
        """Menginisialisasi sensor MPU6050."""
        # Mengatur sample rate dan konfigurasi sensor
        self.bus.write_byte_data(self.device_address, 0x19, 7)  # Sample rate
        self.bus.write_byte_data(self.device_address, 0x6B, 1)  # Aktifkan sensor
        self.bus.write_byte_data(self.device_address, 0x1A, 0)  # Konfigurasi sensor
        self.bus.write_byte_data(self.device_address, 0x1B, 24)  # Konfigurasi gyro
        self.bus.write_byte_data(self.device_address, 0x38, 1)  # Mengaktifkan interrupt
        time.sleep(0.1)  # Tunggu agar sensor stabil
        self._calibrate_offsets()  # Kalibrasi sensor untuk mendapatkan offset

    def _calibrate_offsets(self, samples=100):
        """Kalibrasi sensor untuk mendapatkan offset pada akselerometer."""
        offset_x = offset_y = offset_z = 0
        for _ in range(samples):
            offset_x += self.read_raw_data(0x3B)
            offset_y += self.read_raw_data(0x3D)
            offset_z += self.read_raw_data(0x3F)
            time.sleep(0.01)  # Menunggu sejenak untuk memastikan pembacaan selesai
        self.offset_x = offset_x / samples
        self.offset_y = offset_y / samples
        self.offset_z = offset_z / samples

    def read_raw_data(self, addr):
        """Membaca data raw dari sensor (Accelero dan Gyro)."""
        high = self.bus.read_byte_data(self.device_address, addr)  # Membaca byte tinggi
        low = self.bus.read_byte_data(self.device_address, addr + 1)  # Membaca byte rendah
        value = (high << 8) | low  # Menggabungkan byte tinggi dan rendah
        if value > 32768:  # Jika nilai lebih besar dari 32768, ubah ke format signed
            value -= 65536
        return value

    def read_gyro(self):
        """Membaca data gyro dengan offset."""
        gx = (self.read_raw_data(0x43) - self.offset_x) / 131.0  # Menghitung derajat per detik
        gy = (self.read_raw_data(0x45) - self.offset_y) / 131.0
        gz = (self.read_raw_data(0x47) - self.offset_z) / 131.0
        return gx, gy, gz

    def read_accel(self):
        """Membaca data akselerometer."""
        ax = self.read_raw_data(0x3B) / 16384.0  # Faktor konversi 16384 untuk 2G
        ay = self.read_raw_data(0x3D) / 16384.0
        az = self.read_raw_data(0x3F) / 16384.0
        return ax, ay, az

    def print_data(self):
        """Membaca dan menampilkan data gyro dan akselerometer."""
        gx, gy, gz = self.read_gyro()
        ax, ay, az = self.read_accel()
        
        print(f"Gyro: X={gx:.2f}°/s | Y={gy:.2f}°/s | Z={gz:.2f}°/s")
        print(f"Accel: X={ax:.2f}g | Y={ay:.2f}g | Z={az:.2f}g")
        print("-" * 40)

    def close(self):
        """Menutup koneksi I2C bus."""
        self.bus.close()
