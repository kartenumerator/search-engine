import socket
import time
import sys

def ping_port(ip: str, port: int, timeout: float = 2.0):
    start = time.time()

    try:
        with socket.create_connection((ip, port), timeout=timeout):
            latency = (time.time() - start) * 1000
            print(f"[OPEN] {ip}:{port} responded in {latency:.2f} ms")

    except socket.timeout:
        print(f"[TIMEOUT] {ip}:{port} did not respond within {timeout}s")

    except ConnectionRefusedError:
        print(f"[CLOSED] {ip}:{port} is reachable but port is closed")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    ip = sys.argv[1]
    port = int(sys.argv[2])

    ping_port(ip, port)