import asyncio
import websockets
import json
import base64
import uuid
import ffmpeg
import threading
import os
import logging
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('audio_streaming')

STREAM_URLS = [
   # "http://mediaserv30.live-streams.nl:8086/live",
   "https://s3.us-east-1.amazonaws.com/twilio-calls-recordings/recordings/ACab32b204986a87a022a07b5cf4c95e0f/REaf0c60c181e2f36b0be8a20c80056767",
   "https://mediaserv33.live-streams.nl:8034/live"
]

async def send_flags_to_frontend(ws, stream_uuid, flag_type, sequence_number):
    """ Sends start, media, or stop flags to the frontend. """
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

    logger.info(f"[FLAG] {flag_type} for {stream_uuid}")

    try:
        await ws.send_json(flag)
        logger.info(f"[✅ SENT] {flag_type} sent to frontend")
    except Exception as e:
        logger.error(f"[ERROR] Could not send flag: {e}")

def process_audio(ws, stream_url, stream_uuid, loop):
    """ Runs FFmpeg in a separate thread and sends audio chunks via WebSocket. """
    
    async def send_stop_flag():
        """ Sends stop flag from within the asyncio event loop. """
        await send_flags_to_frontend(ws, stream_uuid, "Stop Flag", 999)

    def run_ffmpeg():
        try:
            logger.info(f"[INFO] Starting FFmpeg for {stream_url}")
            process = (
                ffmpeg.input(stream_url)
                .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=8000)
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

            chunk_counter = 0

            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    logger.error("[ERROR] No audio data received, stopping stream.")
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

                if chunk_counter % 100 == 0:  # Log less frequently
                    logger.info(f"[DEBUG] Sending media chunk {chunk_counter + 1}")

                # Send message using event loop
                future = asyncio.run_coroutine_threadsafe(ws.send_json(message), loop)
                try:
                    future.result(timeout=1.0)  # Wait up to 1 second
                except asyncio.TimeoutError:
                    logger.warning("[WARN] WebSocket send timed out")
                    continue
                except Exception as send_error:
                    logger.error(f"[ERROR] WebSocket send error: {send_error}")
                    break  # Stop sending if WebSocket is closed

                chunk_counter += 1

            process.wait()
            logger.info(f"[INFO] FFmpeg process completed for: {stream_url}")

            if process.returncode != 0:
                error_output = process.stderr.read().decode()
                logger.error(f"[ERROR] FFmpeg failed for {stream_url}: {error_output}")

            # Send Stop Flag after streaming ends
            asyncio.run_coroutine_threadsafe(send_stop_flag(), loop)
            logger.info(f"[FLAG] Stop Flag sent for {stream_uuid}")

        except Exception as e:
            logger.error(f"[ERROR] Streaming {stream_url}: {e}")

    thread = threading.Thread(target=run_ffmpeg, daemon=True)
    thread.start()

# HTTP routes
async def health_check(request):
    """Health check endpoint for monitoring"""
    return web.json_response({
        'status': 'ok', 
        'message': 'Audio streaming server is running'
    })

async def index(request):
    """Simple index page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audio Streaming Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Audio Streaming Server</h1>
        <p>WebSocket server is running. Connect to /ws for the WebSocket endpoint.</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def websocket_handler(request):
    """WebSocket handler for audio streaming"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    logger.info("[INFO] Client connected to WebSocket")
    await ws.send_json({"event": "connected", "protocol": "LiveAudio", "version": "1.0.0"})

    loop = asyncio.get_running_loop()

    for stream_url in STREAM_URLS:
        stream_uuid = str(uuid.uuid4())

        # Send Start Flag before streaming starts
        await send_flags_to_frontend(ws, stream_uuid, "Start Flag", 1)

        # Start FFmpeg processing
        thread = threading.Thread(
            target=process_audio, 
            args=(ws, stream_url, stream_uuid, loop), 
            daemon=True
        )
        thread.start()

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                logger.info(f"Received message: {msg.data[:100]}...")
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket connection closed with exception {ws.exception()}")
    finally:
        logger.info("[INFO] WebSocket connection closed")
    
    return ws

async def main():
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get("PORT", 5000))
    
    # Create web application
    app = web.Application()
    
    # Add routes
    app.add_routes([
        web.get('/', index),
        web.get('/health', health_check),
        web.head('/health', health_check),  # Explicitly handle HEAD requests
        web.get('/ws', websocket_handler),
    ])
    
    # Start the server
    logger.info(f"Starting server on port {port}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Server started successfully on port {port}")
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)  # Sleep for an hour

if __name__ == "__main__":
    asyncio.run(main())