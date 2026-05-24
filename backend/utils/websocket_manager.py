import asyncio
from typing import Dict, List
from fastapi import WebSocket
from utils.logger import logger

class ConnectionManager:
    def __init__(self):
        # Maps bidder_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Cache extracted text so late connections still get documents
        self.extracted_text_cache: Dict[str, list] = {}
        # We need a thread-safe way to send messages because the background task runs in a thread pool.
        # We can store the asyncio event loop where the server runs.
        self.loop = None

    def set_loop(self, loop):
        self.loop = loop
        logger.info("WebSocketManager event loop successfully attached.")

    async def connect(self, bidder_id: str, websocket: WebSocket):
        await websocket.accept()
        if bidder_id not in self.active_connections:
            self.active_connections[bidder_id] = []
        self.active_connections[bidder_id].append(websocket)
        logger.info(f"WebSocket connected for bidder: {bidder_id}. Total active: {len(self.active_connections[bidder_id])}")

        # Send cached documents if available
        if bidder_id in self.extracted_text_cache:
            try:
                await websocket.send_json({
                    "type": "documents_extracted",
                    "documents": self.extracted_text_cache[bidder_id]
                })
            except Exception as e:
                logger.warning(f"Failed to send cached documents: {e}")

    def disconnect(self, bidder_id: str, websocket: WebSocket):
        if bidder_id in self.active_connections:
            if websocket in self.active_connections[bidder_id]:
                self.active_connections[bidder_id].remove(websocket)
            if not self.active_connections[bidder_id]:
                del self.active_connections[bidder_id]
        logger.info(f"WebSocket disconnected for bidder: {bidder_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def _broadcast_async(self, bidder_id: str, message: dict):
        if bidder_id in self.active_connections:
            targets = list(self.active_connections[bidder_id])
            for connection in targets:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending websocket message: {e}")
                    # Auto disconnect
                    try:
                        self.disconnect(bidder_id, connection)
                    except:
                        pass

    def broadcast(self, bidder_id: str, message: dict):
        """Thread-safe broadcast that can be called from synchronous background threads."""
        if bidder_id not in self.active_connections:
            return
        
        if self.loop:
            # Schedule the coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(self._broadcast_async(bidder_id, message), self.loop)
        else:
            # Fallback: if we are already in the event loop thread
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._broadcast_async(bidder_id, message))
                else:
                    asyncio.run(self._broadcast_async(bidder_id, message))
            except Exception as e:
                logger.error(f"Failed to broadcast websocket message thread-safely: {e}")

manager = ConnectionManager()
