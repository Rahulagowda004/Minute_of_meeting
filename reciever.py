# audio_server_receiver.py

import socket
import threading
import os
import platform

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        raw_len = conn.recv(4)
        if not raw_len:
            return
        audio_len = int.from_bytes(raw_len, 'big')

        received = b''
        while len(received) < audio_len:
            chunk = conn.recv(min(4096, audio_len - len(received)))
            if not chunk:
                break
            received += chunk

        os.makedirs("received_audio", exist_ok=True)
        filename = f"received_from_{addr[0]}_{addr[1]}.wav"
        out_path = os.path.join("received_audio", filename)
        with open(out_path, 'wb') as f:
            f.write(received)
        print(f"Saved received audio to {out_path}")

        print("Playing received audio...")
        if platform.system() == 'Windows':
            os.system(f'start {out_path}')
        elif platform.system() == 'Darwin':
            os.system(f'afplay {out_path}')
        else:
            os.system(f'aplay {out_path}')
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 12345))  #10.21.50.10
server.listen()
print("Audio server listening on port 12345...")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
