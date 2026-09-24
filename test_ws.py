import asyncio
import websockets
import json

async def test_ws():
    uri = "wss://web-production-ad4ac.up.railway.app/ws"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"action": "join", "mode": "bookmarklet"}))
            response = await websocket.recv()
            print(f"Respuesta: {response}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_ws())
