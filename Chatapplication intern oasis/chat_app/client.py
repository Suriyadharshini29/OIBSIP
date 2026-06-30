import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 55555


def receive_messages(client):
    """Listen for incoming messages and print them."""
    while True:
        try:
            message = client.recv(1024).decode()
            if not message:
                print("Disconnected from server.")
                break
            print(message, end="", flush=True)
        except (ConnectionResetError, OSError):
            print("Connection lost.")
            break


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Could not connect to server at {HOST}:{PORT}. Is it running?")
        sys.exit(1)

    # Start background thread to receive messages
    thread = threading.Thread(target=receive_messages, args=(client,))
    thread.daemon = True
    thread.start()

    try:
        while True:
            message = input()
            if not message:
                continue
            client.send(message.encode())
            if message.strip().lower() == "/quit":
                print("Leaving chat...")
                break
    except KeyboardInterrupt:
        client.send("/quit".encode())
    finally:
        client.close()


if __name__ == "__main__":
    start_client()
