import binascii
import socket
import threading

self_node_name = "node1"
own_ip = ""
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
            token_handler(message, addr)
        elif protocol == "7777":
            message_handler(message, addr)


def token_handler(message, addr):
    sender_ip = addr[0]
    print(f"Message {message} received from {sender_ip}")

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
        crc = calculate_crc32(message)
        formatted_message = f"7777:naoexiste;{self_node_name};{node_name};{crc};{message}"

        send_message(ip, port, formatted_message)


def message_handler(message, addr):
    sender_ip = addr[0]
    print(f"Message {message} received from {sender_ip}")

    protocol, body = message.split(":")
    control, origin, destiny, crc, message = body.split(";")

    destination = config["destination"]
    ip, port = destination.split(":")

    if destiny == self_node_name:
        crc_control = calculate_crc32(message)

        if not crc == crc_control:
            print(f"Message CRC32 is not correct. Moving forward the error")

            formatted_message = f"{protocol}:NACK;{origin};{destiny};{crc};{message}"

            send_message(ip, port, formatted_message)
        else:
            print(f"Message CRC32 is correct. Moving forward the message")

            formatted_message = f"{protocol}:ACK;{origin};{destiny};{crc};{message}"

            send_message(ip, port, formatted_message)
    else:
        print(f"Message {message} is not for this device. Moving forward.")

        send_message(ip, port, message)


def send_message(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (ip, port))


def calculate_crc32(message: str) -> int:
    dados = message.encode('utf-8')
    crc = binascii.crc32(dados) & 0xFFFFFFFF
    return crc


if __name__ == "__main__":
    config = load_config("config.txt")
    own_ip = get_own_ip()
    threading.Thread(target=server, daemon=True).start()
