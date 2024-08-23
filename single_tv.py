import json
import argparse
import time
from wakeonlan import send_magic_packet
from pywebostv.connection import WebOSClient
from pywebostv.controls import ApplicationControl

def connect_to_tv(ip, mac, url=None, credentials_file='tv_credentials.json', tvs_file='connected_tvs.json'):
    """Connect to an LG webOS TV given its IP and MAC address."""
    
    # Load existing credentials if available
    try:
        with open(credentials_file, 'r') as f:
            credentials_store = json.load(f)
    except FileNotFoundError:
        credentials_store = {}

    connected_tvs = []

    print(f"Attempting to connect to LG TV at IP {ip}")

    # Send Wake-on-LAN command
    send_magic_packet(mac)
    print(f"Sent WOL to LG TV at {mac}")

    # Wait for the TV to wake up
    time.sleep(10)  # Increase this delay if necessary

    # Connect to the TV using PyWebOSTV
    client = WebOSClient(ip)
    store = {}

    # If credentials are already stored, use them
    if ip in credentials_store:
        store['client_key'] = credentials_store[ip]

    try:
        for status in client.register(store):
            if status == WebOSClient.PROMPTED:
                print(f"Please accept the pairing request on your TV at IP: {ip}")
            elif status == WebOSClient.REGISTERED:
                print(f"Connected and registered with TV at IP: {ip}")
    except Exception as e:
        print(f"Failed to connect to LG TV at IP {ip}: {e}")
        return

    # Save the new or updated credentials
    credentials_store[ip] = store['client_key']
    connected_tvs.append({'ip': ip, 'mac': mac})

    # If a URL is provided, open the web browser and navigate to the URL
    if url:
        try:
            app_control = ApplicationControl(client)
            app_control.launch('com.webos.app.browser', {"target": url})
            print(f"Launched browser on TV at IP {ip} and navigated to {url}")
        except Exception as e:
            print(f"Failed to launch browser on TV at IP {ip}: {e}")

    # Save credentials for future use
    with open(credentials_file, 'w') as f:
        json.dump(credentials_store, f)
    print("Credentials saved for future use.")

    # Save the list of connected TVs to a file
    with open(tvs_file, 'w') as f:
        json.dump(connected_tvs, f, indent=4)
    print(f"Connected TVs saved to {tvs_file}.")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Connect to an LG webOS TV using specified IP and MAC address.')
    parser.add_argument('--ip', type=str, required=True, help='The IP address of the LG webOS TV.')
    parser.add_argument('--mac', type=str, required=True, help='The MAC address of the LG webOS TV.')
    parser.add_argument('--url', type=str, help='The URL to open in the web browser on the TV (optional).')
    parser.add_argument('--credentials_file', type=str, default='tv_credentials.json', help='File to store TV credentials.')
    parser.add_argument('--tvs_file', type=str, default='connected_tvs.json', help='File to store the list of connected TVs.')

    args = parser.parse_args()

    # Connect to the specified TV
    connect_to_tv(ip=args.ip, mac=args.mac, url=args.url, credentials_file=args.credentials_file, tvs_file=args.tvs_file)
