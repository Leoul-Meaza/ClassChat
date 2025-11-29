# ClassChat Client
# Connects to server and handles messaging

import socket
import threading
import json
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.running = True
        
    def connect(self):
        # Connect to server
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"[CLIENT] Connected to server at {self.host}:{self.port}")
            
            self.username = input("Enter your username: ").strip()
            self.client_socket.send(self.username.encode('utf-8'))
            
            # Start receive thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()
            
            self.send_messages()
            
        except Exception as e:
            print(f"[CLIENT] Error connecting to server: {e}")
            sys.exit(1)
            
    def receive_messages(self):
        # Listen for messages from server
        while self.running:
            try:
                message_data = self.client_socket.recv(4096).decode('utf-8')
                
                if not message_data:
                    print("\n[CLIENT] Disconnected from server")
                    self.running = False
                    break
                
                try:
                    message = json.loads(message_data)
                    self.display_message(message)
                except json.JSONDecodeError:
                    print(f"\n[CLIENT] Received invalid message format")
                    
            except Exception as e:
                if self.running:
                    print(f"\n[CLIENT] Connection lost")
                break
                
    def display_message(self, message):
        # Display received message
        status = message.get('status')
        sender = message.get('sender')
        receiver = message.get('receiver')
        text = message.get('text')
        
        if status == 'private':
            print(f"\n[PRIVATE] {sender}: {text}")
            
        elif status == 'group':
            print(f"\n[{receiver}] {sender}: {text}")
            
        elif status == 'notification':
            print(f"\n[{receiver}] {text}")
            
        elif status == 'info':
            print(f"\n[INFO] {text}")
            
        elif status == 'error':
            print(f"\n[ERROR] {text}")
            
        else:
            print(f"\n{sender}: {text}")
            
    def send_messages(self):
        # Read user input and send to server
        # Small delay to ensure welcome message appears first
        import time
        time.sleep(0.1)
        
        print("\nCommands:")
        print("  /private <username> <message>  - Send a private message")
        print("  /group <room_name> <message>   - Send a group message")
        print("  /create <room_name>            - Create a new chat room")
        print("  /join <room_name>              - Join an existing chat room")
        print("  /quit                          - Exit the chat")
        print()
        
        while self.running:
            try:
                user_input = input()
                
                if not user_input:
                    continue
                
                message = self.parse_command(user_input)
                
                if message:
                    try:
                        message_json = json.dumps(message)
                        self.client_socket.send(message_json.encode('utf-8'))
                        
                        if message.get('status') == 'quit':
                            print("[CLIENT] Disconnecting...")
                            self.running = False
                            break
                    except Exception:
                        print("[CLIENT] Connection lost")
                        self.running = False
                        break
                        
            except KeyboardInterrupt:
                print("\n[CLIENT] Disconnecting...")
                self.running = False
                break
            except Exception as e:
                print(f"[CLIENT] Error: {e}")
                break
                
        # Close socket
        try:
            self.client_socket.close()
        except:
            pass
            
    def parse_command(self, user_input):
        # Parse user input into JSON message
        if user_input.startswith('/'):
            parts = user_input.split(' ', 2)
            command = parts[0].lower()
            
            if command == '/private':
                if len(parts) < 3:
                    print("[ERROR] Usage: /private <username> <message>")
                    return None
                    
                _, receiver, text = parts
                return {
                    "status": "private",
                    "sender": self.username,
                    "receiver": receiver,
                    "text": text
                }
                
            elif command == '/group':
                if len(parts) < 3:
                    print("[ERROR] Usage: /group <room_name> <message>")
                    return None
                    
                _, room_name, text = parts
                return {
                    "status": "group",
                    "sender": self.username,
                    "receiver": room_name,
                    "text": text
                }
                
            elif command == '/create':
                if len(parts) < 2:
                    print("[ERROR] Usage: /create <room_name>")
                    return None
                    
                room_name = parts[1]
                return {
                    "status": "create",
                    "sender": self.username,
                    "receiver": room_name,
                    "text": ""
                }
                
            elif command == '/join':
                if len(parts) < 2:
                    print("[ERROR] Usage: /join <room_name>")
                    return None
                    
                room_name = parts[1]
                return {
                    "status": "join",
                    "sender": self.username,
                    "receiver": room_name,
                    "text": ""
                }
                
            elif command == '/quit':
                return {
                    "status": "quit",
                    "sender": self.username,
                    "receiver": "",
                    "text": ""
                }
                
            else:
                print(f"[ERROR] Unknown command: {command}")
                return None
                
        else:
            print("[ERROR] Please use a command (e.g., /private, /group, /create, /join)")
            return None

if __name__ == "__main__":
    print(" " * 60)
    print("ClassChat Client")
    print(" " * 60)
    
    client = ChatClient(host='127.0.0.1', port=5555)
    client.connect()
