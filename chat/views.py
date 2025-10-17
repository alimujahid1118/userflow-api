from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from jose import jwt, JWTError
from services.common import db_dependency, SECRET_KEY, ALGORITHM
from auth.models import User
from friends.models import Friendship, FriendshipStatus
from chat.services import manager
import json

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/", response_class=HTMLResponse)
async def chat_page(db: db_dependency, request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return HTMLResponse("<h3>Please log in first.</h3>")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
    except JWTError:
        return HTMLResponse("<h3>Invalid token</h3>")

    # Fetch accepted friends
    friendships = db.query(Friendship).filter(
        ((Friendship.receiver_id == user_id) | (Friendship.requester_id == user_id))
        & (Friendship.status == FriendshipStatus.accepted)
    ).all()

    friends = []
    for f in friendships:
        friend_id = f.requester_id if f.receiver_id == user_id else f.receiver_id
        friend = db.query(User).filter(User.id == friend_id).first()
        if friend:
            friends.append({"id": friend.id, "username": friend.username})

    friends_html = "".join(
        f'<div class="friend" data-id="{f["id"]}">{f["username"]}</div>'
        for f in friends
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Chat</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          display: flex;
          height: 100vh;
          margin: 0;
          background-color: #f5f5f5;
        }}
        #friends-panel {{
          width: 25%;
          background-color: #2f3640;
          color: white;
          padding: 10px;
          box-sizing: border-box;
          overflow-y: auto;
        }}
        .friend {{
          padding: 10px;
          cursor: pointer;
          border-bottom: 1px solid #444;
        }}
        .friend:hover {{
          background-color: #414b57;
        }}
        .friend.active {{
          background-color: #718093;
        }}
        #chat-panel {{
          width: 75%;
          display: flex;
          flex-direction: column;
          background: white;
          border-left: 1px solid #ccc;
        }}
        #chat-header {{
          background: #f0f0f0;
          padding: 15px;
          font-weight: bold;
          border-bottom: 1px solid #ddd;
        }}
        #chat-box {{
          flex: 1;
          padding: 15px;
          overflow-y: auto;
          background-color: #fafafa;
        }}
        .message {{
          margin: 5px 0;
          padding: 8px 12px;
          border-radius: 8px;
          max-width: 70%;
          word-wrap: break-word;
        }}
        .me {{
          background-color: #d1f7c4;
          margin-left: auto;
        }}
        .them {{
          background-color: #eaeaea;
        }}
        #chat-input {{
          display: flex;
          padding: 10px;
          border-top: 1px solid #ddd;
          background: #f9f9f9;
        }}
        #message-input {{
          flex: 1;
          padding: 8px;
          border: 1px solid #ccc;
          border-radius: 5px;
        }}
        #send-btn {{
          margin-left: 10px;
          padding: 8px 16px;
          background-color: #4caf50;
          border: none;
          color: white;
          border-radius: 5px;
          cursor: pointer;
        }}
        #send-btn:hover {{
          background-color: #45a049;
        }}
      </style>
    </head>
    <body>
      <div id="friends-panel">
        <h3>Your Friends</h3>
        {friends_html if friends_html else "<p>No friends yet.</p>"}
      </div>

      <div id="chat-panel">
        <div id="chat-header">Select a friend to chat</div>
        <div id="chat-box"></div>
        <div id="chat-input">
          <input type="text" id="message-input" placeholder="Type your message...">
          <button id="send-btn">Send</button>
        </div>
      </div>

      <script>
        const ws = new WebSocket(`ws://${{window.location.host}}/chat/ws`);
        const chatBox = document.getElementById("chat-box");
        const chatHeader = document.getElementById("chat-header");
        const messageInput = document.getElementById("message-input");
        const sendBtn = document.getElementById("send-btn");
        let currentFriendId = null;
        let chats = {{}};

        // Select friend
        document.querySelectorAll(".friend").forEach(friendEl => {{
          friendEl.addEventListener("click", () => {{
            document.querySelectorAll(".friend").forEach(f => f.classList.remove("active"));
            friendEl.classList.add("active");

            currentFriendId = parseInt(friendEl.dataset.id);
            chatHeader.textContent = "Chat with " + friendEl.textContent;
            renderChat(currentFriendId);
          }});
        }});

        // Render chat messages
        function renderChat(friendId) {{
          chatBox.innerHTML = "";
          const messages = chats[friendId] || [];
          messages.forEach(msg => {{
            const div = document.createElement("div");
            div.classList.add("message", msg.sender === "me" ? "me" : "them");
            div.textContent = msg.text;
            chatBox.appendChild(div);
          }});
          chatBox.scrollTop = chatBox.scrollHeight;
        }}

        // Handle incoming WebSocket messages
        ws.onmessage = (event) => {{
          const data = JSON.parse(event.data);

          if (data.type === "message") {{
            const {{ sender_id, sender_name, content }} = data;

            if (!chats[sender_id]) {{
              chats[sender_id] = [];
            }}

            chats[sender_id].push({{
              sender: "them",
              text: content
            }});

            if (currentFriendId === sender_id) {{
              renderChat(sender_id);
            }}
          }}
        }};

        // Send message
        sendBtn.onclick = () => {{
          const text = messageInput.value.trim();
          if (!text || !currentFriendId) {{
            alert("Select a friend and type a message.");
            return;
          }}
          ws.send(JSON.stringify({{ text: text, recipients: [currentFriendId] }}));

          if (!chats[currentFriendId]) {{
            chats[currentFriendId] = [];
          }}
          chats[currentFriendId].push({{ sender: "me", text: text }});
          renderChat(currentFriendId);
          messageInput.value = "";
        }};
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================================
# WebSocket Endpoint
# ============================================================
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: db_dependency):
    """
    Handles WebSocket connections:
    - Authenticates user via JWT
    - Loads their friends
    - Allows sending messages to selected friends only
    """
    # Get JWT token from cookies
    token = websocket.cookies.get("access_token")
    if token is None:
        await websocket.close(code=1008)
        return

    # Decode JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        username = payload.get("sub")
    except JWTError as e:
        print("JWT error:", e)
        await websocket.close(code=1008)
        return

    # Validate user
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        await websocket.close(code=1008)
        return

    # Load accepted friends
    friendships = db.query(Friendship).filter(
        ((Friendship.receiver_id == db_user.id) | (Friendship.requester_id == db_user.id))
        & (Friendship.status == FriendshipStatus.accepted)
    ).all()

    friend_ids = [
        f.requester_id if f.receiver_id == db_user.id else f.receiver_id
        for f in friendships
    ]

    # Register connection
    await manager.connect(websocket, user_id, friend_ids, db)
    await manager.send_personal_message(f"Welcome {username}!", websocket)

    try:
        # Chat loop
        while True:
          raw_data = await websocket.receive_text()

          try:
              message_data = json.loads(raw_data)
              if not isinstance(message_data, dict):
                  raise ValueError("Invalid JSON format")

              text = message_data.get("text")
              recipients = message_data.get("recipients", [])
          except Exception as e:
              print("Invalid message received:", raw_data, "Error:", e)
              await websocket.send_text("Invalid message format. Expected JSON.")
              continue

          if not text:
              continue

          message = f"{username}: {text}"

          # Send message to selected friends
          await manager.send_to_selected_friends(user_id, recipients, message, db)

          # # Echo message to sender
          # await websocket.send_text(message)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.send_to_friends(user_id, f"{username} left the chat")
