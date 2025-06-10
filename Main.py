import binascii
import cmd
import socket
import threading
import time
from collections import deque

from TokenHandler import TokenHandler, TooManyTokensException, TimeoutException

PORT = 5000
config = None
fila = deque()
messages = []
has_token = False
sent_message: str = ""

token_module: TokenHandler = TokenHandler()


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


def server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))

    while True:
        data, addr = sock.recvfrom(1024)

        message = data.decode().strip()
        protocol = message.split(':')[0]

        print(message)

        if protocol == "9000":
            token_handler(message, addr)
        elif protocol == "7777":
            message_handler(message, addr)


def token_server():
    if config["token"]:
        global has_token
        has_token = True

        while True:
            print("Verifying token timeout...")

            try:
                token_module.check_token_timeout()
            except TimeoutException:
                print(f"ERROR: Timeout. Reinitializing token.")
                start_token()
            time.sleep(5)


def token_handler(message, addr):
    token_module.reset_token_time()

    global has_token
    has_token = True

    sender_ip = addr[0]
    print(f"Message {message} received from {sender_ip}")

    destination = config["destination"]
    node_name = config["node_name"]
    ip, port = destination.split(":")

    time.sleep(config["token_time"])

    if len(fila) == 0:
        print(f"No messages to send. Moving forward token to {destination}")

        send_message(ip, int(port), "9000")
    else:
        message = fila.popleft()
        text, destiny_node_name = message.split(":")
        print(f"Sending {text} to {destination}")

        crc = calculate_crc32(text)
        formatted_message = f"7777:naoexiste;{node_name};{destiny_node_name};{crc};{text}"

        global sent_message
        sent_message = formatted_message

        send_message(ip, int(port), formatted_message)


def message_handler(message, addr):
    sender_ip = addr[0]
    print(f"Message {message} received from {sender_ip}")

    protocol, body = message.split(":")
    control, origin, destiny, crc, message = body.split(";")

    destination = config["destination"]
    ip, port = destination.split(":")

    time.sleep(config["token_time"])

    if validate_message(body):
        global sent_message
        sent_message = ""
        send_message(ip, int(port), "9000")
    elif destiny == "TODOS":
        print(f"Broadcast message received. Moving forward the message.")



    elif destiny == config.get("node_name"):
        crc_control = calculate_crc32(message)

        if not crc == crc_control:
            print(f"Message CRC32 is not correct. Moving forward the error")

            formatted_message = f"{protocol}:NACK;{origin};{destiny};{crc};{message}"

            send_message(ip, int(port), formatted_message)
        else:
            print(f"Message CRC32 is correct. Moving forward the message")

            formatted_message = f"{protocol}:ACK;{origin};{destiny};{crc};{message}"

            send_message(ip, int(port), formatted_message)
    else:
        print(f"Message {message} is not for this device. Moving forward.")

        send_message(ip, int(port), message)


def send_message(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (ip, port))


def calculate_crc32(message: str) -> int:
    data = message.encode('utf-8')
    crc = binascii.crc32(data) & 0xFFFFFFFF
    return crc


def validate_message(received_body: str) -> bool:
    global sent_message

    if not sent_message or ":" not in sent_message:
        return False

    protocol, body = sent_message.split(":")
    control, origin, destiny, crc, message = body.split(";")
    control_string = f"{origin}:{destiny};{crc};{message}"

    received_control, received_origin, received_destiny, received_crc, received_message = received_body.split(";")
    control_received_string = f"{received_origin}:{received_destiny};{received_crc};{received_message}"

    if control_string == control_received_string and not received_control == "naoexiste":
        return True
    else:
        return False


def start_token():
    if config["token"]:
        print("This device has ownership of the token.")
        print("Starting token and sending to the device on the right.")
        token_module.start_token_time()

        destination = config["destination"]
        ip, port = destination.split(":")

        send_message(ip, int(port), "9000")


def run_server():
    threading.Thread(target=server, daemon=True).start()
    threading.Thread(target=token_server, daemon=True).start()


class Interface(cmd.Cmd):
    intro = "Bem-vindo ao nó da rede! Digite 'help' para ver os comandos disponíveis."
    prompt = ">>> "

    def do_add_message(self, arg):
        try:
            fila.append(arg)
            print(f"Mensagem enfileirada: {arg}")
        except ValueError:
            print("Uso: add_message \"mensagem\"")

    def do_status(self, arg):
        print(f"Nome do nó: {config['node_name']}")
        print(f"Destino configurado: {config['destination']}")
        print(f"Responsável pelo token? {config['token']}")
        print(f"Tempo do token {config['token_time']}")
        print(f"Mensagens pendentes: {messages}")

    def do_exit(self, arg):
        print("Encerrando...")
        return True

    def do_start(self, arg):
        start_token()
        run_server()
        print("Servidor iniciado em background.")


if __name__ == "__main__":
    config = load_config("config.txt")
    Interface().cmdloop()
