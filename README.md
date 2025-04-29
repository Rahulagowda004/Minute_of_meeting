# Minute of Meeting

A voice activity detection and audio transmission system for capturing and sharing meeting audio.

## Overview

This project implements a voice-triggered audio recording and transmission system. It automatically detects when someone is speaking during a meeting, captures that audio, and periodically sends it to a receiver for playback or storage.

## Features

- **Voice Activity Detection (VAD)**: Automatically detects when speech is occurring
- **Real-time Audio Processing**: Captures audio using your system's microphone
- **Buffered Recording**: Includes padding before and after speech to avoid clipping
- **Periodic Transmission**: Sends recorded speech segments at configurable intervals
- **Client-Server Architecture**: Separate components for audio capture and reception

## Components

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

### 3. Basic Chat Client/Server (`sender.py`)

A simple text messaging client/server implementation.

## Requirements

```
sounddevice
numpy
webrtcvad
requests
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/username/Minute_of_meeting.git
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Rahul A Gowda (2025)
