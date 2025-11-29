# ClassChat

A multi-threaded TCP chat server and client built with Python sockets. Supports private messaging and group chat rooms.

## Features

- Private one-on-one messaging
- Group chat rooms
- Multi-threaded server handles concurrent connections
- JSON-based message protocol
- Real-time message delivery

## Getting Started

### Prerequisites

Python 3.7+

### Running the Server

python3 server.py

The server listens on `127.0.0.1:5555`.

### Running a Client

python3 client.py

You'll be prompted to enter a username. Each client needs a unique username.

## Usage

### Commands

/private <username> <message>    Send a private message
/create <room_name>              Create a new chat room
/join <room_name>                Join an existing chat room
/group <room_name> <message>     Send a message to a chat room
/quit                            Disconnect from server

### Example

# Alice creates a room
/create study-group

# Bob joins the room
/join study-group

# Alice sends a group message
/group study-group Hey everyone!

# Alice sends Bob a private message
/private Bob Want to work on the project together?

## Implementation Details

The system uses a client-server architecture where all communication is routed through a central server.

**Server**
- Handles multiple clients using threading (one thread per connection)
- Maintains dictionaries of active users and chat rooms
- Routes messages based on message type (private/group)
- Thread-safe operations using locks

**Client**
- Two threads: one for sending, one for receiving
- Parses user commands into JSON format
- Displays incoming messages with appropriate formatting

**Message Format**

All messages are JSON objects with four fields:

{
  "status": "private|group|create|join|quit",
  "sender": "username",
  "receiver": "recipient or room_name",
  "text": "message content"
}

## License

MIT
