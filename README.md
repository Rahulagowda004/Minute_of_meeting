## Features

- **Voice Activity Detection (VAD)**: Automatically detects when speech is occurring
- **Real-time Audio Processing**: Captures audio using your system's microphone
- **Buffered Recording**: Includes padding before and after speech to avoid clipping
- **Periodic Transmission**: Sends recorded speech segments at configurable intervals
- **Client-Server Architecture**: Separate components for audio capture and reception

### 1. VAD Sender (`vad_sender.py`)

The main audio capture component that:
- Listens for speech using WebRTC VAD
- Records detected speech with configurable padding
- Transmits captured audio at regular intervals (default: 30 seconds)

### 2. Receiver (`reciever.py`)

The server component that:
- Listens for incoming audio transmissions
- Saves received audio as WAV files
- Automatically plays back received audio


## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Rahulagowda004/Minute_of_meeting.git
   cd Minute_of_meeting
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Key configuration parameters in `vad_sender.py`:
- `SAMPLE_RATE`: Audio sample rate (16000 Hz default)
- `VAD_MODE`: Sensitivity of voice detection (0-3, 3 is most aggressive)
- `SEND_INTERVAL_SEC`: How often to send audio chunks (30 seconds default)
- `SERVER_IP`: IP address of the receiving server
- `SERVER_PORT`: Port of the receiving server

## Usage

### Start the receiver
```
python reciever.py
```

### Start the VAD sender
```
python vad_sender.py
```

The system will begin listening for speech, capturing audio when speech is detected, and sending it to the configured server every 30 seconds.

