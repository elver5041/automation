import socket

def get_ip():
    """gets the ip of the machine"""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return "127.0.0.1"
