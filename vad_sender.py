# sender.py

import sounddevice as sd
import numpy as np
import webrtcvad
import socket
import threading
import time
import queue
import wave
import io
import os
from datetime import datetime

# Configuration parameters
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 30
PADDING_DURATION_MS = 300
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
VAD_MODE = 3
SEND_INTERVAL_SEC = 30
SERVER_IP = '10.21.50.10'
SERVER_PORT = 12345

audio_queue = queue.Queue()
speech_segments = []
is_speaking = False
last_speaking_time = 0
last_send_time = 0
stop_event = threading.Event()

vad = webrtcvad.Vad(VAD_MODE)

def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"Audio callback status: {status}")
    audio_int16 = (indata * 32767).astype(np.int16)
    audio_queue.put(audio_int16.copy())

def process_audio():
    global is_speaking, last_speaking_time, speech_segments
    speech_frames = []
    silence_frames = 0
    while not stop_event.is_set():
        try:
            frame = audio_queue.get(timeout=1)
            frame_bytes = frame.tobytes()
            is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
            if is_speech:
                silence_frames = 0
                if not is_speaking:
                    print("Speech detected!")
                    is_speaking = True
                    padding_frames = min(len(speech_frames), int(PADDING_DURATION_MS / FRAME_DURATION_MS))
                    if padding_frames > 0:
                        speech_segments.extend(speech_frames[-padding_frames:])
                speech_segments.append(frame)
                last_speaking_time = time.time()
            else:
                silence_frames += 1
                if is_speaking and silence_frames < int(PADDING_DURATION_MS / FRAME_DURATION_MS):
                    speech_segments.append(frame)
                elif is_speaking:
                    print("Speech ended.")
                    is_speaking = False
            speech_frames.append(frame)
            if len(speech_frames) > int(PADDING_DURATION_MS / FRAME_DURATION_MS):
                speech_frames.pop(0)
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in audio processing: {e}")

def send_audio_periodically():
    global speech_segments, last_send_time
    os.makedirs("sent_audio", exist_ok=True)
    os.makedirs("pending_audio", exist_ok=True)

    while not stop_event.is_set():
        current_time = time.time()

        if (current_time - last_send_time >= SEND_INTERVAL_SEC) and speech_segments:
            try:
                audio_data = np.concatenate(speech_segments)
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(CHANNELS)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(SAMPLE_RATE)
                    wav_file.writeframes(audio_data.tobytes())
                wav_data = wav_buffer.getvalue()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"audio_{timestamp}.wav"

                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.settimeout(5)
                    client.connect((SERVER_IP, SERVER_PORT))
                    client.send(len(wav_data).to_bytes(4, 'big'))
                    client.sendall(wav_data)
                    client.close()
                    print(f"Sent {len(wav_data)} bytes of audio data")
                    with open(os.path.join("sent_audio", filename), 'wb') as f:
                        f.write(wav_data)
                except Exception as e:
                    print(f"Failed to send audio, saving to pending_audio: {e}")
                    with open(os.path.join("pending_audio", filename), 'wb') as f:
                        f.write(wav_data)

                speech_segments = []
                last_send_time = current_time
            except Exception as e:
                print(f"Unexpected error while handling audio send: {e}")

        try:
            for pending_file in os.listdir("pending_audio"):
                pending_path = os.path.join("pending_audio", pending_file)
                with open(pending_path, 'rb') as f:
                    data = f.read()
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.settimeout(5)
                    client.connect((SERVER_IP, SERVER_PORT))
                    client.send(len(data).to_bytes(4, 'big'))
                    client.sendall(data)
                    client.close()
                    print(f"Resent pending file: {pending_file}")
                    os.remove(pending_path)
                except Exception as retry_err:
                    print(f"Retry failed for {pending_file}: {retry_err}")
                    break
        except Exception as e:
            print(f"Error while resending pending files: {e}")

        time.sleep(1)

def main():
    global last_send_time
    print("Starting Voice Activity Detection system...")
    os.makedirs("sent_audio", exist_ok=True)
    os.makedirs("pending_audio", exist_ok=True)
    last_send_time = time.time()

    audio_thread = threading.Thread(target=process_audio)
    audio_thread.daemon = True
    audio_thread.start()

    sender_thread = threading.Thread(target=send_audio_periodically)
    sender_thread.daemon = True
    sender_thread.start()

    try:
        with sd.InputStream(callback=audio_callback, channels=CHANNELS,
                            samplerate=SAMPLE_RATE, blocksize=FRAME_SIZE,
                            dtype='float32'):
            print(f"Listening for speech... (VAD mode: {VAD_MODE})")
            print("Press Ctrl+C to stop")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error in audio stream: {e}")
    finally:
        stop_event.set()
        print("VAD system stopped.")

if __name__ == "__main__":
    main()
