import socket
import threading

def receive(sock):
    while True:
        try:
            data = sock.recv(1024)
            print("Received:", data.decode())
        except:
            break

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('10.21.50.10', 12345))

threading.Thread(target=receive, args=(client,), daemon=True).start()

while True:
    msg = input("You: ")
    client.send(msg.encode())
