from fastapi import WebSocket
from sqlalchemy.orm import Session
from typing import Dict, List

from chat.models import Message
from auth.models import User


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_friends: Dict[int, List[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, friends: list[int], db: Session):
        """Accept connection and deliver any pending messages."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_friends[user_id] = friends

        await self.deliver_pending_messages(user_id, db)

    def disconnect(self, user_id: int):
        """Remove user from active connections."""
        self.active_connections.pop(user_id, None)
        self.user_friends.pop(user_id, None)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a direct message to a connected WebSocket."""
        await websocket.send_text(message)

    async def send_to_selected_friends(self, sender_id: int, recipients: list[int], message: str, db: Session):
        """Send message to selected friends or store if offline."""
        sender = db.query(User).filter(User.id == sender_id).first()

        for recipient_id in recipients:
            # Save the message to the database first
            msg = Message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=message,
                delivered=False
            )
            db.add(msg)
            db.commit()

            if recipient_id in self.active_connections:
                # Recipient is online — send via WebSocket
                ws = self.active_connections[recipient_id]
                await ws.send_json({
                    "type": "message",
                    "sender_id": sender_id,
                    "sender_name": sender.username,
                    "content": message,
                    "timestamp": str(msg.timestamp)
                })
                msg.delivered = True  # Mark as delivered
                db.commit()

    async def deliver_pending_messages(self, user_id: int, db: Session):
        """Deliver undelivered messages when a user reconnects."""
        pending = (
            db.query(Message)
            .filter_by(recipient_id=user_id, delivered=False)
            .order_by(Message.timestamp.asc())
            .all()
        )

        if not pending:
            return

        ws = self.active_connections[user_id]
        for msg in pending:
            sender = db.query(User).filter(User.id == msg.sender_id).first()
            await ws.send_json({
                "type": "message",
                "sender_id": msg.sender_id,
                "sender_name": sender.username if sender else "Unknown",
                "content": msg.content,
                "timestamp": str(msg.timestamp)
            })
            msg.delivered = True

        db.commit()


# ✅ Global instance
manager = ConnectionManager()
