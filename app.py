import asyncio
import websockets
import json
import base64
import uuid
import ffmpeg
import threading
import os
from aiohttp import web

# Ports
WS_PORT = 5000
HTTP_PORT = int(os.environ.get("PORT", 8000))

# Streams
STREAM_URLS = [
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

    try:
        await ws.send(json.dumps(flag))
    except websockets.exceptions.ConnectionClosed:
        print("[ERROR] WebSocket closed while sending flag")

def process_audio(ws, stream_url, stream_uuid, loop):
    async def send_stop_flag():
        await send_flags_to_frontend(ws, stream_uuid, "Stop Flag", 999)

    def run_ffmpeg():
        try:
            process = (
                ffmpeg.input(stream_url)
                .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=8000)
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

            chunk_counter = 0
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
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

                future = asyncio.run_coroutine_threadsafe(ws.send(json.dumps(message)), loop)
                try:
                    future.result()
                except Exception:
                    break

                chunk_counter += 1

            process.wait()
            asyncio.run_coroutine_threadsafe(send_stop_flag(), loop)

        except Exception as e:
            print(f"[ERROR] FFmpeg processing failed: {e}")

    threading.Thread(target=run_ffmpeg, daemon=True).start()

async def handle_connection(ws):
    try:
        await ws.send(json.dumps({"event": "connected", "protocol": "LiveAudio", "version": "1.0.0"}))
        loop = asyncio.get_running_loop()

        for stream_url in STREAM_URLS:
            stream_uuid = str(uuid.uuid4())
            await send_flags_to_frontend(ws, stream_uuid, "Start Flag", 1)
            threading.Thread(target=process_audio, args=(ws, stream_url, stream_uuid, loop), daemon=True).start()

        while True:
            await asyncio.sleep(1)

    except websockets.exceptions.ConnectionClosed:
        print("[INFO] Client disconnected")

# Health check HTTP server
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_servers():
    # Start health check HTTP server
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    print(f"[INFO] HTTP health check running on port {HTTP_PORT}")

    # Start WebSocket server
    ws_server = await websockets.serve(handle_connection, "0.0.0.0", WS_PORT)
    print(f"[INFO] WebSocket server running on port {WS_PORT}")
    await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_servers())
