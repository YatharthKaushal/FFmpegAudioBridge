# FFmpegAudioBridge

FFmpegAudioBridge is a Python-based WebSocket server designed to stream audio from remote URLs to connected clients in real-time. Leveraging FFmpeg for robust audio processing and WebSocket for low-latency communication, this project enables seamless audio streaming with structured event handling for start, media, and stop flags. It is ideal for applications requiring live audio broadcasting, such as remote audio monitoring, live radio streaming, or real-time audio analysis.

## Features

- **Real-Time Audio Streaming**: Streams audio from HTTP/HTTPS URLs using FFmpeg, delivering chunks to clients via WebSocket.
- **Structured Event System**: Sends `Start`, `Media`, and `Stop` flags to clients, ensuring clear communication of stream states.
- **Multi-Stream Support**: Configurable to handle multiple audio streams sequentially, with unique stream identifiers.
- **Efficient Audio Processing**: Converts audio to WAV format (PCM 16-bit, mono, 8kHz) for compatibility and performance.
- **Asynchronous and Threaded Design**: Uses `asyncio` for WebSocket handling and threading for non-blocking FFmpeg processing.

## Use Cases

- Live audio streaming for web applications.
- Real-time audio processing for IoT or monitoring systems.
- Prototyping audio-based services with minimal setup.

## Getting Started

### Prerequisites

- Python 3.11+
- FFmpeg installed on the host system
- Dependencies: `websockets`, `ffmpeg-python` (install via `pip install -r requirements.txt`)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/FFmpegAudioBridge.git
   cd FFmpegAudioBridge
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure FFmpeg is installed:
   - On Ubuntu: `sudo apt-get install ffmpeg`
   - On macOS: `brew install ffmpeg`

### Running the Server

1. Update the `STREAM_URLS` list in the script with your audio stream URLs.
2. Run the server:

   ```bash
   python main.py
   ```

3. The WebSocket server will start at `ws://https://ffmpegaudiobridge.onrender.com:5000`.

### Connecting a Client

- Use a WebSocket client (e.g., a JavaScript-based frontend) to connect to `ws://https://ffmpegaudiobridge.onrender.com:5000`.
- The server sends a `connected` event upon connection, followed by `start`, `media`, and `stop` events for each stream.

## Deployment

FFmpegAudioBridge can be deployed on platforms supporting Python and FFmpeg, such as:

- **Render**: Use a `Dockerfile` to bundle FFmpeg and Python dependencies.
- **Fly.io**: Deploy with Docker for persistent WebSocket connections.
- Ensure the platform supports WebSocket and has sufficient resources for FFmpeg.

## Example Deployment (Render)

1. Create a `Dockerfile`:

   ```dockerfile
   FROM python:3.11-slim
   RUN apt-get update && apt-get install -y ffmpeg
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 5000
   CMD ["python", "main.py"]
   ```

2. Push to a GitHub repository and deploy via Render's Web Service.

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for bug fixes, features, or improvements.
