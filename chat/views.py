from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from services.common import db_dependency
from auth.models import User
from chat.services import manager
from jose import jwt, JWTError
from services.common import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/chat", tags=["chat"])

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet" crossorigin="anonymous" />
    </head>
    <body>
        <div class="container mt-3">
            <h1>Messenger</h1>
            <form onsubmit="sendMessage(event)">
                <input type="text" id="textMessage" autocomplete="off" class="form-control" placeholder="Type your message here..." />
                <button class="btn btn-outline-primary mt-2">Send</button>
            </form>
            <ul class="container mt-5 list-unstyled" id="Messages"></ul>
        </div>
        <script>
            const protocol = window.location.protocol === "https:" ? "wss" : "ws";
            const ws = new WebSocket(`${protocol}://${window.location.host}/chat/ws`);

            ws.onmessage = function(event) {
                const messages = document.getElementById("Messages");
                const message = document.createElement("li");
                message.textContent = event.data;
                messages.appendChild(message);
            };

            function sendMessage(event) {
                const input = document.getElementById("textMessage");
                ws.send(input.value);
                input.value = "";
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""

@router.get("/")
async def get():
    return HTMLResponse(html)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: db_dependency):
    token = websocket.cookies.get("access_token")
    print("Token from websocket:", token)
    if token is None:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        username = payload.get("sub")
    except JWTError as e:
        print("JWT error:", e)
        await websocket.close(code=1008)
        return

    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    await manager.broadcast(f"{username} joined the chat")

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{username} left the chat")