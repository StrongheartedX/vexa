# load_test_client.py
import asyncio
import websockets
import numpy as np
import soundfile as sf
import argparse
import os
import random
import time
import logging
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
CHUNK_SIZE = 8192  # Bytes to send at a time (adjust as needed)
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DTYPE = 'float32'
SIMULATED_DELAY_SECONDS = (CHUNK_SIZE / (SAMPLE_RATE * np.dtype(AUDIO_DTYPE).itemsize * CHANNELS)) # Simulate real-time


async def receive_messages(websocket, client_id):
    """Listens for messages from the server."""
    message_count = 0
    try:
        async for message in websocket:
            message_count += 1
            # In a real test, you might parse/validate the message
            logging.debug(f"Client {client_id}: Received message {message_count}")
            # Add detailed logging if needed: logging.debug(f"Client {client_id}: Data: {message[:100]}...")
    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"Client {client_id}: Connection closed normally.")
    except websockets.exceptions.ConnectionClosedError as e:
        logging.error(f"Client {client_id}: Connection closed with error: {e}")
    except Exception as e:
        logging.error(f"Client {client_id}: Error receiving messages: {e}")
    finally:
        logging.info(f"Client {client_id}: Received a total of {message_count} messages.")
    return message_count

async def run_client(client_id, server_url, audio_file):
    """Simulates a single client connecting and streaming an audio file."""
    websocket = None
    message_count = 0
    connection_start_time = time.time()
    stream_start_time = None
    audio_duration = 0
    client_uid = str(uuid.uuid4())
    logging.info(f"Client {client_id}: Starting - UID {client_uid} - File {os.path.basename(audio_file)}")

    try:
        # --- Read Audio File ---
        try:
            with sf.SoundFile(audio_file, 'r') as f:
                if f.samplerate != SAMPLE_RATE:
                    logging.warning(f"Client {client_id}: Audio file {audio_file} has sample rate {f.samplerate}, expected {SAMPLE_RATE}. Ensure server can handle or resample.")
                if f.channels != CHANNELS:
                     logging.warning(f"Client {client_id}: Audio file {audio_file} has {f.channels} channels, expected {CHANNELS}. Ensure server can handle or convert to mono.")
                # Read entire file - adjust if files are very large
                audio_data = f.read(dtype=AUDIO_DTYPE)
                audio_duration = len(audio_data) / SAMPLE_RATE
        except Exception as e:
            logging.error(f"Client {client_id}: Failed to read audio file {audio_file}: {e}")
            return False, 0, 0, 0 # success, messages, audio_duration, processing_time

        # --- Connect to Server ---
        websocket = await websockets.connect(server_url, open_timeout=10, close_timeout=10)
        logging.info(f"Client {client_id}: Connected to {server_url}")

        # --- Start Receiving Task ---
        receiver_task = asyncio.create_task(receive_messages(websocket, client_id))

        # --- Send Initial Config ---
        config_message = {
            "uid": client_uid,
            "language": None,  # Or specify: "en", "ru", etc.
            "task": "transcribe",
            "model": "large-v3", # Should match server if relevant
            "use_vad": True
        }
        await websocket.send(str(config_message).replace("'", "\"")) # Send JSON string
        logging.info(f"Client {client_id}: Sent initial config.")

        # --- Stream Audio Chunks ---
        stream_start_time = time.time()
        bytes_sent = 0
        num_chunks = (len(audio_data) * audio_data.itemsize + CHUNK_SIZE - 1) // CHUNK_SIZE

        for i in range(num_chunks):
            start_byte = i * CHUNK_SIZE
            end_byte = start_byte + CHUNK_SIZE
            chunk = audio_data.flat[start_byte:end_byte].tobytes() # Get bytes slice

            if not chunk:
                break

            await websocket.send(chunk)
            bytes_sent += len(chunk)
            logging.debug(f"Client {client_id}: Sent chunk {i+1}/{num_chunks} ({len(chunk)} bytes)")

            # Simulate real-time pacing
            await asyncio.sleep(SIMULATED_DELAY_SECONDS)

        logging.info(f"Client {client_id}: Finished streaming {bytes_sent} bytes ({num_chunks} chunks) for {os.path.basename(audio_file)}")

        # --- Wait for processing / server disconnect ---
        # Option 1: Send an "EOS" message if server expects one
        # await websocket.send('{"event": "EOS"}')
        # Option 2: Just wait for receiver task to finish or connection closes
        await asyncio.sleep(5) # Wait a bit for final messages
        await websocket.close(reason='Client finished streaming')
        logging.info(f"Client {client_id}: WebSocket closed.")

        message_count = await receiver_task
        processing_time = time.time() - stream_start_time if stream_start_time else 0
        return True, message_count, audio_duration, processing_time

    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"Client {client_id}: Connection closed before finishing.")
        if websocket and not receiver_task.done():
             await websocket.close()
             message_count = await receiver_task # Get messages received before close
        return False, message_count, audio_duration, time.time() - stream_start_time if stream_start_time else 0
    except Exception as e:
        logging.error(f"Client {client_id}: FAILED with error: {e}", exc_info=True)
        if websocket and not websocket.closed:
             await websocket.close(code=1011, reason=f'Client error: {e}')
        if 'receiver_task' in locals() and not receiver_task.done():
             receiver_task.cancel() # Attempt to cancel receiver task
             try:
                 await receiver_task
             except asyncio.CancelledError:
                 pass
             except Exception as rex:
                 logging.error(f"Client {client_id}: Error during receiver task cancellation: {rex}")

        return False, 0, audio_duration, time.time() - stream_start_time if stream_start_time else 0 # Indicate failure


async def main(args):
    """Runs multiple clients concurrently."""
    server_url = f"ws://{args.host}:{args.port}"
    logging.info(f"Starting load test with {args.num_clients} clients targeting {server_url}")
    logging.info(f"Using audio files from: {args.audio_dir}")

    try:
        audio_files = [os.path.join(args.audio_dir, f) for f in os.listdir(args.audio_dir) if f.lower().endswith('.wav')]
        if not audio_files:
            logging.error(f"No .wav files found in {args.audio_dir}")
            return
        logging.info(f"Found {len(audio_files)} audio files.")
    except FileNotFoundError:
        logging.error(f"Audio directory not found: {args.audio_dir}")
        return
    except Exception as e:
        logging.error(f"Error listing audio files: {e}")
        return

    start_time = time.time()
    tasks = []
    for i in range(args.num_clients):
        audio_file = random.choice(audio_files)
        tasks.append(run_client(i + 1, server_url, audio_file))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()

    # --- Process Results ---
    successful_clients = 0
    total_messages = 0
    total_audio_duration = 0
    total_processing_time = 0
    failed_clients = 0

    for i, result in enumerate(results):
        client_id = i + 1
        if isinstance(result, Exception):
            logging.error(f"Client {client_id}: Task raised an exception: {result}")
            failed_clients += 1
        else:
            success, msg_count, audio_dur, proc_time = result
            if success:
                successful_clients += 1
                total_messages += msg_count
                total_audio_duration += audio_dur
                total_processing_time += proc_time
            else:
                failed_clients +=1
                logging.warning(f"Client {client_id}: Task reported failure (received {msg_count} messages).")
                total_messages += msg_count # Count messages even on failure


    logging.info("----- Load Test Summary -----")
    logging.info(f"Total duration: {end_time - start_time:.2f} seconds")
    logging.info(f"Target clients: {args.num_clients}")
    logging.info(f"Successful clients: {successful_clients}")
    logging.info(f"Failed clients: {failed_clients}")
    logging.info(f"Total messages received: {total_messages}")
    if successful_clients > 0:
         logging.info(f"Average audio duration processed per successful client: {total_audio_duration / successful_clients:.2f} seconds")
         logging.info(f"Average processing time per successful client: {total_processing_time / successful_clients:.2f} seconds")
    logging.info("---------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhisperLive Load Test Client")
    parser.add_argument("--num-clients", type=int, default=5, help="Number of concurrent clients")
    parser.add_argument("--host", type=str, default="load-balancer", help="Server hostname (service name in Docker Compose)")
    parser.add_argument("--port", type=int, default=80, help="Server port (Nginx internal port)")
    parser.add_argument("--audio-dir", type=str, default="/app/test_audio", help="Directory containing .wav audio files")
    # Add more arguments if needed (e.g., test duration, language)

    args = parser.parse_args()
    asyncio.run(main(args)) 