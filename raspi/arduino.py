import minimalmodbus
import time

class ModbusSensor:
    def __init__(self, slaveaddress=1, port='/dev/ttyUSB0'):
        """Inisialisasi sensor Modbus dengan port dan alamat slave yang sesuai."""
        self.instrument = minimalmodbus.Instrument(port, slaveaddress)  # Port dan alamat slave
        self.instrument.serial.baudrate = 9600
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1  # Timeout dalam detik

    def read_register_data(self, register_address):
        """Membaca data dari register Modbus dan menampilkannya."""
        try:
            registers = self.instrument.read_registers(register_address, 1)  # Membaca 1 register mulai dari register_address
            value = 2.25 * registers[0] - 838.85
            return value
        except Exception as e:
            print("Error:", e)  # Menangani error jika gagal membaca data
            return 0

    def close(self):
        """Menutup koneksi serial."""
        self.instrument.serial.close()

    def run(self):
        """Menjalankan loop pembacaan data secara terus-menerus."""
        try:
            while True:
                self.read_register_data(0)  # Membaca data dari register 0
                time.sleep(1)  # Tunggu 1 detik sebelum membaca lagi
        except KeyboardInterrupt:
            print("\nProgram dihentikan.")
        finally:
            self.close()  # Menutup koneksi saat program dihentikan
