import socket
import os
import sys
import logging
import ssl
import shutil

def make_socket(destination_address='172.16.16.101', port=8885):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")
        return None

def make_secure_socket(destination_address='localhost', port=10000):
    try:
        # get it from https://curl.se/docs/caextract.html

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        secure_socket = context.wrap_socket(sock, server_hostname=destination_address)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")


def send_command(command_str, server_address, is_secure=False):
    alamat_server = server_address[0]
    port_server = server_address[1]
    if is_secure == True:
        sock = make_secure_socket(alamat_server, port_server)
    else:
        sock = make_socket(alamat_server, port_server)
    sock.settimeout(5)
    
    try:
        sock.sendall(command_str.encode())
        data_received = b""
        while True:
            data = sock.recv(4096)
            if data:
                data_received += data
                if len(data) < 4096:
                    break
            else:
                break
        return data_received.decode(errors="ignore")
    except Exception as ee:
        logging.warning(f"error during data receiving {str(ee)}")
        return f"Error: {str(ee)}"
    finally:
        sock.close()

def get_command(server_address, dir=''):
    command = f"GET /{dir} HTTP/1.0\r\n\r\n"
    result = send_command(command, server_address)
    print(result)
    return result

def post_command(server_address, filename):
    try:
        with open(filename, "rb") as f:
            content = f.read()

        headers = [
            f"POST /files HTTP/1.0",
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(filename)}\"",
            f"Content-Length: {len(content)}",
            ""
        ]
        command = "\r\n".join(headers).encode() + b"\r\n" + content + b"\r\n\r\n"
        
        sock = make_socket(server_address[0], server_address[1])
        if not sock:
            return "Connection failed"
        
        try:
            sock.sendall(command)
            data_received = b""
            while True:
                data = sock.recv(4096)
                if data:
                    data_received += data
                    if len(data) < 4096:
                        break
                else:
                    break
            result = data_received.decode(errors="ignore")
            print(result)
            return result
        except Exception as ee:
            logging.warning(f"error during data receiving {str(ee)}")
            return f"Error: {str(ee)}"
        finally:
            sock.close()
            
    except FileNotFoundError:
        print(f"Error: Local file '{filename}' not found.")
        return "File not found"
    except Exception as e:
        print(f"An error occurred during upload: {e}")
        return f"Error: {str(e)}"

def delete_command(server_address, filename):
    command = f"DELETE /files/{filename} HTTP/1.0\r\n\r\n"
    result = send_command(command, server_address)
    print(result)
    return result

if __name__ == "__main__":
    server_addr = ('localhost', 8889)
    
    print("===================LIST FILES===================")
    get_command(server_addr, '')
    print("===================UPLOAD FILES===================")
    # post_command(server_addr, 'test_upload.txt')
    delete_command(server_addr, 'test_upload.txt')
    # post_command(server_addr, 'donalbebek.jpg')
    print("===================LIST FILES===================")
    get_command(server_addr, '')

    # get_command(server_addr, 'donalbebek.jpg')
    # delete_command(server_addr, 'donalbebek.jpg')
    # get_command(server_addr, 'donalbebek.jpg')
    # get_command(server_addr, 'page.html')
    # get_command(server_addr, '')