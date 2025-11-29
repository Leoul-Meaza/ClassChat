# ClassChat Server
# Handles multiple clients, routes messages, manages chat rooms

import socket
import threading
import json

class ChatServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Track connected clients and chat rooms
        self.clients = {}
        self.chat_rooms = {}
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
    def start(self):
        # Start server and listen for connections
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"[SERVER] Server started on {self.host}:{self.port}")
        print("[SERVER] Waiting for connections...")
        
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[SERVER] New connection from {address}")
                
                # Handle each client in a new thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.start()
                
            except Exception as e:
                print(f"[SERVER] Error accepting connection: {e}")
                
    def handle_client(self, client_socket):
        # Handle communication with a single client
        username = None
        disconnected = False
        
        try:
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            # Check if username already exists
            with self.lock:
                if username in self.clients:
                    error_msg = json.dumps({
                        "status": "error",
                        "sender": "SERVER",
                        "receiver": username,
                        "text": "Username already taken. Please disconnect and try again."
                    })
                    client_socket.send(error_msg.encode('utf-8'))
                    client_socket.close()
                    return
                
                self.clients[username] = client_socket
                
            print(f"[SERVER] {username} has joined the chat")
            
            # Send welcome message
            welcome_msg = json.dumps({
                "status": "info",
                "sender": "SERVER",
                "receiver": username,
                "text": f"Welcome to ClassChat, {username}!"
            })
            client_socket.send(welcome_msg.encode('utf-8'))
            
            # Handle messages from client
            while True:
                try:
                    message_data = client_socket.recv(4096).decode('utf-8')
                    
                    if not message_data:
                        break
                        
                    try:
                        message = json.loads(message_data)
                        if message.get('status') == 'quit':
                            disconnected = True
                            self.disconnect_client(username)
                            break
                        else:
                            self.route_message(message, username)
                    except json.JSONDecodeError:
                        print(f"[SERVER] Invalid JSON from {username}")
                        
                except Exception as e:
                    if not disconnected:
                        print(f"[SERVER] {username} disconnected unexpectedly")
                    break
                    
        except Exception as e:
            if not disconnected:
                print(f"[SERVER] Error handling client {username}: {e}")
            
        finally:
            if not disconnected:
                self.disconnect_client(username)
            
    def route_message(self, message, sender_username):
        # Route message to appropriate handler
        status = message.get('status')
        receiver = message.get('receiver')
        text = message.get('text')
        
        if status == 'private':
            self.handle_private_message(sender_username, receiver, text)
            
        elif status == 'group':
            self.handle_group_message(sender_username, receiver, text)
            
        elif status == 'create':
            self.handle_create_room(sender_username, receiver)
            
        elif status == 'join':
            self.handle_join_room(sender_username, receiver)
            
    def handle_private_message(self, sender, receiver, text):
        # Send private message from one user to another
        with self.lock:
            if receiver not in self.clients:
                error_msg = json.dumps({
                    "status": "error",
                    "sender": "SERVER",
                    "receiver": sender,
                    "text": f"User '{receiver}' not found."
                })
                self.clients[sender].send(error_msg.encode('utf-8'))
                return
            
            message = json.dumps({
                "status": "private",
                "sender": sender,
                "receiver": receiver,
                "text": text
            })
            
            try:
                self.clients[receiver].send(message.encode('utf-8'))
                print(f"[SERVER] Private message from {sender} to {receiver}")
            except Exception as e:
                print(f"[SERVER] Error sending to {receiver}: {e}")
                
    def handle_group_message(self, sender, room_name, text):
        # Broadcast message to all members of chat room
        with self.lock:
            if room_name not in self.chat_rooms:
                error_msg = json.dumps({
                    "status": "error",
                    "sender": "SERVER",
                    "receiver": sender,
                    "text": f"Chat room '{room_name}' does not exist."
                })
                self.clients[sender].send(error_msg.encode('utf-8'))
                return
            
            if sender not in self.chat_rooms[room_name]:
                error_msg = json.dumps({
                    "status": "error",
                    "sender": "SERVER",
                    "receiver": sender,
                    "text": f"You are not a member of '{room_name}'."
                })
                self.clients[sender].send(error_msg.encode('utf-8'))
                return
            
            message = json.dumps({
                "status": "group",
                "sender": sender,
                "receiver": room_name,
                "text": text
            })
            
            for member in self.chat_rooms[room_name]:
                if member in self.clients:
                    try:
                        self.clients[member].send(message.encode('utf-8'))
                    except Exception as e:
                        print(f"[SERVER] Error sending to {member}: {e}")
                        
            print(f"[SERVER] Group message in {room_name} from {sender}")
            
    def handle_create_room(self, creator, room_name):
        # Create a new chat room
        with self.lock:
            if room_name in self.chat_rooms:
                error_msg = json.dumps({
                    "status": "error",
                    "sender": "SERVER",
                    "receiver": creator,
                    "text": f"Chat room '{room_name}' already exists."
                })
                self.clients[creator].send(error_msg.encode('utf-8'))
                return
            
            self.chat_rooms[room_name] = [creator]
            
            success_msg = json.dumps({
                "status": "info",
                "sender": "SERVER",
                "receiver": creator,
                "text": f"Chat room '{room_name}' created successfully!"
            })
            self.clients[creator].send(success_msg.encode('utf-8'))
            
            print(f"[SERVER] {creator} created room '{room_name}'")
            
    def handle_join_room(self, username, room_name):
        # Add user to existing chat room
        with self.lock:
            if room_name not in self.chat_rooms:
                error_msg = json.dumps({
                    "status": "error",
                    "sender": "SERVER",
                    "receiver": username,
                    "text": f"Chat room '{room_name}' does not exist."
                })
                self.clients[username].send(error_msg.encode('utf-8'))
                return
            
            if username in self.chat_rooms[room_name]:
                info_msg = json.dumps({
                    "status": "info",
                    "sender": "SERVER",
                    "receiver": username,
                    "text": f"You are already a member of '{room_name}'."
                })
                self.clients[username].send(info_msg.encode('utf-8'))
                return
            
            self.chat_rooms[room_name].append(username)
            
            success_msg = json.dumps({
                "status": "info",
                "sender": "SERVER",
                "receiver": username,
                "text": f"You joined '{room_name}'."
            })
            self.clients[username].send(success_msg.encode('utf-8'))
            
            # Notify other room members
            notification = json.dumps({
                "status": "notification",
                "sender": "SERVER",
                "receiver": room_name,
                "text": f"{username} has joined the room."
            })
            
            for member in self.chat_rooms[room_name]:
                if member != username and member in self.clients:
                    try:
                        self.clients[member].send(notification.encode('utf-8'))
                    except Exception as e:
                        print(f"[SERVER] Error notifying {member}: {e}")
                        
            print(f"[SERVER] {username} joined room '{room_name}'")
            
    def disconnect_client(self, username):
        # Remove client and clean up data
        if not username:
            return
            
        with self.lock:
            if username not in self.clients:
                return
            
            # Remove from all chat rooms
            for room_name, members in list(self.chat_rooms.items()):
                if username in members:
                    members.remove(username)
                    
                    notification = json.dumps({
                        "status": "notification",
                        "sender": "SERVER",
                        "receiver": room_name,
                        "text": f"{username} has left the room."
                    })
                    
                    for member in members:
                        if member in self.clients:
                            try:
                                self.clients[member].send(notification.encode('utf-8'))
                            except:
                                pass
                    
                    # Remove empty rooms
                    if not members:
                        del self.chat_rooms[room_name]
            
            # Remove from clients and close socket
            if username in self.clients:
                try:
                    self.clients[username].close()
                except:
                    pass
                del self.clients[username]
                
            print(f"[SERVER] {username} disconnected")


if __name__ == "__main__":
    server = ChatServer()
    print(" " * 60)
    print("ClassChat Server")
    print(" " * 60)
    server.start()
