import socket
import json
import argparse
from zeroconf import Zeroconf, ServiceBrowser
from wakeonlan import send_magic_packet
from pywebostv.connection import WebOSClient
from pywebostv.controls import ApplicationControl

class LGTVListener:
    def __init__(self):
        self.devices = []

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            address = socket.inet_ntoa(info.address)
            mac = ':'.join(info.properties[b'mac'].decode('utf-8')[i:i+2] for i in range(0, 12, 2))
            self.devices.append({
                'name': name,
                'ip': address,
                'mac': mac
            })

def discover_lg_tvs():
    zeroconf = Zeroconf()
    listener = LGTVListener()
    ServiceBrowser(zeroconf, "_lg-smart-tv._tcp.local.", listener)
    zeroconf.close()
    return listener.devices

def wake_on_lan_and_connect(tvs, url=None, credentials_file='tv_credentials.json', tvs_file='connected_tvs.json'):
    # Load existing credentials if available
    try:
        with open(credentials_file, 'r') as f:
            credentials_store = json.load(f)
    except FileNotFoundError:
        credentials_store = {}

    connected_tvs = []

    for tv in tvs:
        ip = tv['ip']
        mac = tv['mac']
        name = tv['name']

        # Send Wake-on-LAN command
        send_magic_packet(mac)
        print(f"Sent WOL to {name} at {mac}")

        # Connect to the TV using PyWebOSTV
        client = WebOSClient(ip)
        store = {}

        # If credentials are already stored, use them
        if ip in credentials_store:
            store['client_key'] = credentials_store[ip]

        for status in client.register(store):
            if status == WebOSClient.PROMPTED:
                print(f"Please accept the pairing request on your TV: {name}")
            elif status == WebOSClient.REGISTERED:
                print(f"Connected and registered with TV: {name}")

        # Save the new or updated credentials
        credentials_store[ip] = store['client_key']
        connected_tvs.append(tv)

        # If a URL is provided, open the web browser and navigate to the URL
        if url:
            app_control = ApplicationControl(client)
            app_control.launch('com.webos.app.browser', {"target": url})
            print(f"Launched browser on {name} and navigated to {url}")

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
    parser = argparse.ArgumentParser(description='Discover, wake, and control LG webOS TVs on your network.')
    parser.add_argument('url', type=str, help='The URL to open in the web browser on the TV.')
    parser.add_argument('--credentials_file', type=str, default='tv_credentials.json', help='File to store TV credentials.')
    parser.add_argument('--tvs_file', type=str, default='connected_tvs.json', help='File to store the list of connected TVs.')

    args = parser.parse_args()

    # Discover all LG webOS TVs on the network
    tvs = discover_lg_tvs()
    if tvs:
        print("Discovered LG TVs on the network:")
        for tv in tvs:
            print(f"- {tv['name']} (IP: {tv['ip']}, MAC: {tv['mac']})")
        
        # Wake on LAN, connect to discovered TVs, and open the browser with the URL
        wake_on_lan_and_connect(tvs, url=args.url, credentials_file=args.credentials_file, tvs_file=args.tvs_file)
    else:
        print("No LG webOS TVs found on the network.")
