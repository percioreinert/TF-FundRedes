import socket
import threading

PORT = 5000
config = None
messages = []


def load_config(file_path: str) -> dict:
    with open(file_path, "r") as file:
        lines = [line.strip() for line in file.readlines()]

    node_config = {
        "destination": lines[0],
        "node_name": lines[1],
        "token_time": int(lines[2]),
        "token": lines[3].lower() == "true"
    }
    return node_config


def get_own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))

    while True:
        data, addr = sock.recvfrom(1024)

        message = data.decode().strip()
        protocol = message.split(' ')[0]

        if protocol == "9000":
            token(data, addr)
        elif protocol == "7777":
            "data"


def token(data, addr):
    sender_ip = addr[0]
    print(f"Message received from {sender_ip}")
    destination = config["destination"]
    node_name = config["node_name"]
    ip, port = destination.split(":")

    if len(messages) == 0:
        print(f"No messages to send. Moving forward token to {destination}")

        send_message(ip, port, "9000")
    else:
        message = messages[0]
        print(f"Sending {messages} to {destination}")

        # ver como descobrir o nome do nodo da máquina destino
        # ver como calcular o CRC da mensagem e colocar na mensagem formatada
        formatted_message = f"7777:naoexiste;{node_name};destination_node;CRC;{message}"

        send_message(ip, port, formatted_message)


def send_message(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (ip, port))


if __name__ == "__main__":
    config = load_config("config.txt")
    threading.Thread(target=server, daemon=True).start()
