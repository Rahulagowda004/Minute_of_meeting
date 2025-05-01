
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
SAMPLE_RATE = 16000  # WebRTC VAD requires 8kHz, 16kHz, 32kHz or 48kHz
CHANNELS = 1  # Mono audio
FRAME_DURATION_MS = 30  # VAD works with 10, 20, or 30 ms frames
PADDING_DURATION_MS = 300  # Padding duration at the beginning and end of speech
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
VAD_MODE = 3  # VAD sensitivity mode (0-3, 3 is the most aggressive)
SEND_INTERVAL_SEC = 30  # Send audio chunks every 30 seconds
SERVER_IP = '10.21.50.10'  # Server IP address from your receiver.py
SERVER_PORT = 12345  # Server port from your receiver.py

# Queues and flags for thread communication
audio_queue = queue.Queue()
speech_segments = []  # Store detected speech segments
is_speaking = False
last_speaking_time = 0
last_send_time = 0
stop_event = threading.Event()

# Initialize VAD
vad = webrtcvad.Vad(VAD_MODE)

def audio_callback(indata, frames, time_info, status):
    """Callback function for audio stream"""
    if status:
        print(f"Audio callback status: {status}")
    # Convert float32 audio to int16 for VAD
    audio_int16 = (indata * 32767).astype(np.int16)
    audio_queue.put(audio_int16.copy())

def process_audio():
    """Process audio frames and detect speech"""
    global is_speaking, last_speaking_time, speech_segments
    
    print("VAD processing started...")
    speech_frames = []
    silence_frames = 0
    
    while not stop_event.is_set():
        try:
            frame = audio_queue.get(timeout=1)
            
            # Convert to bytes for VAD
            frame_bytes = frame.tobytes()
            
            # Check if speech is detected
            try:
                is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
            except Exception as e:
                print(f"VAD error: {e}")
                continue
            
            if is_speech:
                silence_frames = 0
                if not is_speaking:
                    print("Speech detected!")
                    is_speaking = True
                    # Add some padding before speech starts
                    padding_frames = min(len(speech_frames), int(PADDING_DURATION_MS / FRAME_DURATION_MS))
                    if padding_frames > 0:
                        speech_segments.extend(speech_frames[-padding_frames:])
                
                speech_segments.append(frame)
                last_speaking_time = time.time()
            else:
                silence_frames += 1
                # Keep adding frames for a short period after speech ends
                if is_speaking and silence_frames < int(PADDING_DURATION_MS / FRAME_DURATION_MS):
                    speech_segments.append(frame)
                elif is_speaking:
                    print("Speech ended.")
                    is_speaking = False
            
            # Keep a rolling buffer of recent frames for padding
            speech_frames.append(frame)
            if len(speech_frames) > int(PADDING_DURATION_MS / FRAME_DURATION_MS):
                speech_frames.pop(0)
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in audio processing: {e}")

def send_audio_periodically():
    """Send accumulated speech segments to the server periodically"""
    global speech_segments, last_send_time
    
    print("Audio sender started...")
    
    while not stop_event.is_set():
        current_time = time.time()
        
        # Send audio if 30 seconds have passed and we have speech segments
        if (current_time - last_send_time >= SEND_INTERVAL_SEC) and speech_segments:
            try:
                # Create audio data from speech segments
                if speech_segments:
                    print(f"Preparing to send {len(speech_segments)} speech segments...")
                    
                    # Convert speech segments to a single numpy array
                    audio_data = np.concatenate(speech_segments)
                    
                    # Create WAV file in memory
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, 'wb') as wav_file:
                        wav_file.setnchannels(CHANNELS)
                        wav_file.setsampwidth(2)  # 2 bytes for int16
                        wav_file.setframerate(SAMPLE_RATE)
                        wav_file.writeframes(audio_data.tobytes())
                    
                    # Get the WAV data
                    wav_data = wav_buffer.getvalue()
                    
                    # Connect to server and send audio
                    print(f"Connecting to server at {SERVER_IP}:{SERVER_PORT}...")
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((SERVER_IP, SERVER_PORT))
                    
                    # Send data length as 4 bytes first
                    data_length = len(wav_data)
                    client.send(data_length.to_bytes(4, 'big'))
                    
                    # Send the WAV data
                    client.sendall(wav_data)
                    print(f"Sent {data_length} bytes of audio data")
                    
                    # Close the connection
                    client.close()
                    
                    # Save a local copy for debugging (optional)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = os.path.join("sent_audio", f"sent_audio_{timestamp}.wav")
                    with open(out_path, 'wb') as f:
                        f.write(wav_data)
                    
                    # Reset speech segments
                    speech_segments = []
                    
                last_send_time = current_time
            except Exception as e:
                print(f"Error sending audio: {e}")
        
        # Sleep for a bit to avoid high CPU usage
        time.sleep(1)

def main():
    """Main function to start the VAD system"""
    global last_send_time
    
    print("Starting Voice Activity Detection system...")
    last_send_time = time.time()
    
    # Start the audio processing thread
    audio_thread = threading.Thread(target=process_audio)
    audio_thread.daemon = True
    audio_thread.start()
    
    # Start the audio sending thread
    sender_thread = threading.Thread(target=send_audio_periodically)
    sender_thread.daemon = True
    sender_thread.start()
    
    try:
        # Start capturing audio
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
        # Stop all threads gracefully
        stop_event.set()
        print("VAD system stopped.")

if __name__ == "__main__":
    main()