import serial
import time
import json
import os
from dotenv import load_dotenv
import paramiko
from scp import SCPClient

# Cargar las variables de entorno del archivo .env
load_dotenv()

# Configuración del puerto serie y la velocidad en baudios
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyACM0')  # Cambia esto al puerto correcto o usa variable de entorno
BAUD_RATE = int(os.getenv('BAUD_RATE', 9600))

# Configuración del servidor SSH desde variables de entorno
SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = int(os.getenv('SSH_PORT', 22))  # Puerto SSH por defecto
SSH_USER = os.getenv('SSH_USER')
SSH_PASS = os.getenv('SSH_PASS')
REMOTE_PATH = os.getenv('REMOTE_PATH', '/path/to/remote/directory')

def read_from_serial():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    time.sleep(2)  # Espera a que la conexión se establezca
    print("Conexión establecida, iniciando lectura de datos...")
    
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                print(f"Línea recibida: {line}")
                if line.startswith('T =') and ', H =' in line:
                    try:
                        parts = line.split(',')
                        temperature = float(parts[0].split('=')[1].strip().split(' ')[0])
                        humidity = float(parts[1].split('=')[1].strip().split('%')[0])
                        data = {"temperature": temperature, "humidity": humidity, "timestamp": time.time()}
                        print(f"Datos leídos: {data}")
                        return data  # Devuelve los datos y sale de la función
                    except ValueError:
                        print("Error de lectura: datos no válidos")
            else:
                print("Esperando datos...")
            time.sleep(1)  # Espera 1 segundo antes de verificar de nuevo
    except Exception as e:
        print(f"Error durante la lectura del puerto serie: {e}")
    finally:
        ser.close()
        print("Puerto serie cerrado.")
    return None

def save_to_json(data, filename='data.json'):
    try:
        # Obtiene el directorio del script actual
        script_dir = os.path.dirname(__file__)
        # Construye la ruta completa al archivo JSON
        filepath = os.path.join(script_dir, filename)

        # Leer datos existentes y agregar nuevos datos
        if os.path.exists(filepath):
            with open(filepath, 'r') as json_file:
                existing_data = json.load(json_file)
        else:
            existing_data = []

        existing_data.append(data)

        # Guardar los datos actualizados
        with open(filepath, 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)
        
        print(f"Datos guardados en {filepath}")
        return filepath
    except Exception as e:
        print(f"Error al guardar los datos en JSON: {e}")
        return None

def send_file_via_ssh(local_file):
    try:
        print(f"Enviando {local_file} al servidor {SSH_HOST}...")
        # Configuración de la conexión SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS)
        
        # Uso de SCP para transferir el archivo
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_file, REMOTE_PATH)
        print(f"Archivo {local_file} enviado correctamente a {REMOTE_PATH} en el servidor {SSH_HOST}.")
    except Exception as e:
        print(f"Error al enviar el archivo vía SSH: {e}")
    finally:
        ssh.close()

def main():
    print("Leyendo datos desde el puerto serie...")
    data = read_from_serial()
    
    if data:
        print("Guardando datos en el archivo JSON...")
        local_file = save_to_json(data)
        if local_file:
            send_file_via_ssh(local_file)
    else:
        print("No se leyeron datos válidos.")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # Espera 60 segundos antes de la próxima ejecución

