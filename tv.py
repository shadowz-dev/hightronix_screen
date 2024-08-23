import socket
import json
import argparse
import time
from scapy.all import ARP, Ether, srp
from wakeonlan import send_magic_packet
from pywebostv.connection import WebOSClient
from pywebostv.controls import ApplicationControl

def arp_scan_network(ip_range):
    """Perform an ARP scan to identify all devices on the local network."""
    arp_request = ARP(pdst=ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=10, verbose=False)[0]

    devices = []
    for sent, received in answered_list:
        print(f"Found device - IP: {received.psrc}, MAC: {received.hwsrc}")
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    return devices

def is_lg_webos_tv(mac_address):
    """Check if the device's MAC address belongs to an LG webOS TV."""
    lg_mac_prefixes = [
        "00:1C:98", "04:18:D6", "18:00:2D", "1C:5A:6B",
        "40:B8:37", "40:B8:9A", "44:A7:CF", "6C:2E:85",
        "78:5D:C8", "A8:23:FE", "AC:9B:0A", "B0:03:65",
        "B8:9E:FC", "CC:44:63", "D0:59:E4", "E8:50:8B",
        "EC:1F:72", "F4:F5:A5", "F8:77:B8", "FC:09:D8",
        "D4:8D:26", "04:09:86"
    ]
    mac_prefix = mac_address[:8].upper()
    return mac_prefix in lg_mac_prefixes

def discover_lg_tvs(ip_range):
    """Discover LG TVs using ARP scanning."""
    arp_devices = arp_scan_network(ip_range)
    lg_tvs = []

    for device in arp_devices:
        ip = device['ip']
        mac = device['mac']
        if is_lg_webos_tv(mac):
            lg_tvs.append(device)
            print(f"Discovered LG webOS TV at IP {ip}, MAC {mac}")

    return lg_tvs

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
        name = tv.get('name', 'LG TV')

        print(f"Attempting to connect to {name} at IP {ip}")

        # Send Wake-on-LAN command
        send_magic_packet(mac)
        print(f"Sent WOL to {name} at {mac}")

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
                    print(f"Please accept the pairing request on your TV: {name}")
                elif status == WebOSClient.REGISTERED:
                    print(f"Connected and registered with TV: {name}")
        except Exception as e:
            print(f"Failed to connect to {name} at IP {ip}: {e}")
            continue

        # Save the new or updated credentials
        credentials_store[ip] = store['client_key']
        connected_tvs.append(tv)

        # If a URL is provided, open the web browser and navigate to the URL
        if url:
            try:
                app_control = ApplicationControl(client)
                app_control.launch('com.webos.app.browser', {"target": url})
                print(f"Launched browser on {name} and navigated to {url}")
            except Exception as e:
                print(f"Failed to launch browser on {name}: {e}")

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
    parser.add_argument('--url', type=str, help='The URL to open in the web browser on the TV (optional).')
    parser.add_argument('--credentials_file', type=str, default='tv_credentials.json', help='File to store TV credentials.')
    parser.add_argument('--tvs_file', type=str, default='connected_tvs.json', help='File to store the list of connected TVs.')
    parser.add_argument('--ip_range', type=str, required=True, help='The IP range to scan (e.g., 192.168.1.0/24).')

    args = parser.parse_args()

    # Discover all LG webOS TVs on the network
    tvs = discover_lg_tvs(args.ip_range)
    if tvs:
        print("Discovered LG TVs on the network:")
        for tv in tvs:
            print(f"- {tv.get('name', 'LG TV')} (IP: {tv['ip']}, MAC: {tv['mac']})")
        
        # Wake on LAN, connect to discovered TVs, and optionally open the browser with the URL
        wake_on_lan_and_connect(tvs, url=args.url, credentials_file=args.credentials_file, tvs_file=args.tvs_file)
    else:
        print("No LG webOS TVs found on the network.")
