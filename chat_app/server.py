import socket
import threading

HOST = "127.0.0.1"
PORT = 55555

clients = []
names = []


def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except:
                remove_client(client)


def remove_client(client):
    if client in clients:
        index = clients.index(client)
        clients.remove(client)
        name = names[index]
        names.remove(name)
        broadcast(f"[Server] {name} has left the chat.\n".encode())
        print(f"{name} disconnected.")
        client.close()


def handle_client(client, address):
    try:
        client.send("Enter your name: ".encode())
        name = client.recv(1024).decode().strip()
        names.append(name)
        clients.append(client)
        print(f"{name} connected from {address}")
        broadcast(f"[Server] {name} joined the chat.\n".encode(), sender=client)
        client.send(f"[Server] Welcome, {name}! Type your messages below.\n".encode())

        while True:
            message = client.recv(1024)
            if not message:
                break
            text = message.decode().strip()
            if text.lower() == "/quit":
                break
            formatted = f"[{name}]: {text}\n"
            print(formatted, end="")
            broadcast(formatted.encode(), sender=client)
    except ConnectionResetError:
        pass
    finally:
        remove_client(client)


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            client, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, address))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
