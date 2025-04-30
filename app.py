import asyncio
import websockets
import json
import base64
import uuid
import ffmpeg
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Health check HTTP server for Render
class SimpleHealthHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    httpd = HTTPServer(('0.0.0.0', 8000), SimpleHealthHandler)
    print("[INFO] Health check HTTP server running on port 8000")
    httpd.serve_forever()

# WebSocket-related setup
STREAM_URLS = [
    # "http://mediaserv30.live-streams.nl:8086/live",
    "https://s3.us-east-1.amazonaws.com/twilio-calls-recordings/recordings/ACab32b204986a87a022a07b5cf4c95e0f/REaf0c60c181e2f36b0be8a20c80056767",
    "https://mediaserv33.live-streams.nl:8034/live"
]

async def send_flags_to_frontend(ws, stream_uuid, flag_type, sequence_number):
    flag = {
        "event": flag_type.lower(),
        "sequenceNumber": str(sequence_number),
        "flag_type": flag_type,
        "streamSid": stream_uuid
    }
    if flag_type == "Start Flag":
        flag["start"] = {"streamSid": stream_uuid}
    elif flag_type == "Stop Flag":
        flag["stop"] = {"streamSid": stream_uuid}

    print(f"\n[FLAG] {flag_type} -> {json.dumps(flag, indent=2)}\n")
    try:
        await ws.send(json.dumps(flag))
        print(f"[✅ SENT] {flag_type} sent to frontend")
    except websockets.exceptions.ConnectionClosed:
        print("[ERROR] WebSocket connection closed before flag could be sent")

def process_audio(ws, stream_url, stream_uuid, loop):
    async def send_stop_flag():
        await send_flags_to_frontend(ws, stream_uuid, "Stop Flag", 999)

    def run_ffmpeg():
        try:
            print(f"[INFO] Starting FFmpeg for {stream_url}")
            process = (
                ffmpeg.input(stream_url)
                .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=8000)
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

            chunk_counter = 0
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    print("[ERROR] No audio data received, stopping stream.")
                    break

                encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                message = {
                    "event": "media",
                    "sequenceNumber": str(chunk_counter + 2),
                    "media": {
                        "track": "inbound",
                        "chunk": str(chunk_counter + 1),
                        "timestamp": str(chunk_counter * 30),
                        "payload": encoded_chunk
                    },
                    "streamSid": stream_uuid
                }

                print(f"[DEBUG] Sending media chunk {chunk_counter + 1}")
                future = asyncio.run_coroutine_threadsafe(ws.send(json.dumps(message)), loop)
                try:
                    future.result()
                except Exception as send_error:
                    print(f"[ERROR] WebSocket send error: {send_error}")
                    break

                chunk_counter += 1

            process.wait()
            print(f"[INFO] FFmpeg process completed for: {stream_url}")

            if process.returncode != 0:
                error_output = process.stderr.read().decode()
                print(f"[ERROR] FFmpeg failed for {stream_url}: {error_output}")

            asyncio.run_coroutine_threadsafe(send_stop_flag(), loop)
            print(f"\n[FLAG] Stop Flag sent for {stream_uuid}\n")

        except Exception as e:
            print(f"[ERROR] Streaming {stream_url}: {e}")

    thread = threading.Thread(target=run_ffmpeg, daemon=True)
    thread.start()

async def handle_connection(ws):
    try:
        print("[INFO] Client connected")
        await ws.send(json.dumps({"event": "connected", "protocol": "LiveAudio", "version": "1.0.0"}))

        loop = asyncio.get_running_loop()
        for stream_url in STREAM_URLS:
            stream_uuid = str(uuid.uuid4())
            await send_flags_to_frontend(ws, stream_uuid, "Start Flag", 1)
            thread = threading.Thread(target=process_audio, args=(ws, stream_url, stream_uuid, loop), daemon=True)
            thread.start()

        while True:
            await asyncio.sleep(1)

    except websockets.exceptions.ConnectionClosed:
        print("[INFO] Client disconnected")
    finally:
        print("[INFO] WebSocket connection closed")

async def main():
    # Start the HTTP health server
    threading.Thread(target=run_health_server, daemon=True).start()

    # Start the WebSocket server
    print("Starting WebSocket server on ws://0.0.0.0:5000")
    server = await websockets.serve(handle_connection, "0.0.0.0", 5000)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
