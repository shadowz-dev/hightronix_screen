import os
import subprocess
import sys

# Set relative path for adb.exe
ADB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adb", "adb.exe")

def run_adb_command(command):
    """Run adb command using subprocess and return output."""
    try:
        # Prepend the adb.exe path to the command
        full_command = f"{ADB_PATH} {command}"
        output = subprocess.check_output(full_command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {command}: {e.output.decode('utf-8').strip()}")
        return None

def connect_to_device(ip_address):
    """Connect to the Android device over Wi-Fi using ADB."""
    print(f"Connecting to device at {ip_address}...")
    result = run_adb_command(f"connect {ip_address}")
    if result and "connected" in result:
        print(f"Successfully connected to {ip_address}.")
        return True
    else:
        print(f"Failed to connect to {ip_address}.")
        return False

def install_apk(apk_path):
    """Install an APK on the connected device."""
    if not os.path.isfile(apk_path):
        print(f"APK file '{apk_path}' does not exist.")
        return False
    
    print(f"Installing APK '{apk_path}'...")
    result = run_adb_command(f"install {apk_path}")
    if result and "Success" in result:
        print(f"APK '{apk_path}' installed successfully.")
        return True
    else:
        print(f"Failed to install APK '{apk_path}'. Output: {result}")
        return False

def main(ip_address, apk_paths):
    """Main function to connect to the Android device over Wi-Fi and install APKs."""
    # Step 1: Connect over Wi-Fi using the known IP address
    connected = connect_to_device(ip_address)
    if not connected:
        return

    # Step 2: Install the APKs
    for apk_path in apk_paths:
        install_apk(apk_path)

    # Optional: Disconnect after installation
    run_adb_command(f"disconnect {ip_address}")
    print("Disconnected from the device.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <device_ip> <apk1> <apk2> ...")
        sys.exit(1)

    # IP address of the Android device (provided as argument)
    device_ip = sys.argv[1]
    
    # List of APK paths (provided as arguments)
    apk_files = sys.argv[2:]
    
    main(device_ip, apk_files)
