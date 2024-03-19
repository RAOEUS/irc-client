import socket
import sys
import threading
import os
from datetime import datetime
import ssl  # Import SSL module

# Function to display help message
def display_help():
    print("Usage: python app.py <host> <port> <nickname> <channel> [<account> <password>] [-tls]")
    print("Example: python app.py irc.libera.chat 6697 nick \"#ricecakes\" my_libera_account my_password -tls")
    print("Example (no authentication): python app.py irc.libera.chat 6697 nick \"#channel\" -tls")

# Check if TLS/SSL flag is provided
use_tls = '-tls' in sys.argv

# Function to connect to the IRC server and authenticate with NickServ if account credentials are provided
def connect_to_server(host, port, nickname, channel, account=None, password=None):
    if use_tls:
        irc_socket = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    else:
        irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    irc_socket.connect((host, port))

    # Send nickname
    irc_socket.send(f'NICK {nickname}\r\n'.encode())
    irc_socket.send(f'USER {nickname} 0 * :{nickname}\r\n'.encode())

    # Receive welcome message
    welcome_message = irc_socket.recv(2048).decode().rstrip()
    print(welcome_message)

    # Authenticate with NickServ if account credentials are provided
    if account and password:
        irc_socket.send(f'PRIVMSG NickServ :IDENTIFY {account} {password}\r\n'.encode())
        while True:
            auth_response = irc_socket.recv(2048).decode().rstrip()
            print(auth_response)
            if "You are now identified" in auth_response:
                break

    # Join the channel
    irc_socket.send(f'JOIN {channel}\r\n'.encode())
    join_response = irc_socket.recv(2048).decode().rstrip()
    print(join_response)

    return irc_socket


# Function to send messages to the channel
def send_message(irc_socket, message, channel):
    # Escape colon and newline characters in the message
    message = message.replace(':', ':%').replace('\n', ' ')
    irc_socket.send(f'PRIVMSG {channel} :{message}\r\n'.encode())


# Function to receive and display messages
def receive_messages(irc_socket, channel, nickname):
    while True:
        message = irc_socket.recv(2048).decode().rstrip()
        if message.startswith('PING'):
            irc_socket.send('PONG\r\n'.encode())
        elif 'PRIVMSG' in message:
            parts = message.split('PRIVMSG')[1].split(':', 1)  # Split message into two parts
            if len(parts) == 2:
                user = message.split('!')[0][1:]
                msg_content = parts[1]  # Content starts after the first colon
                timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
                formatted_message = f'\033[1m{timestamp} {channel} \033[92m<{user}>\033[0m: {msg_content}'
                if nickname in msg_content:
                    formatted_message = f'\033[1m{timestamp} {channel} \033[91m<{user}>\033[0m: {msg_content}'
                print(formatted_message)
            else:
                print("Error: Malformed message")

# Function to get user input and send messages
def send_input(irc_socket, channel, nickname):
    while True:
        message = input()
        send_message(irc_socket, message, channel)
        sys.stdout.write('\033[F\033[K')  # Move cursor up one line and clear the line
        timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        formatted_message = f'\033[1m{timestamp} {channel} \033[93m<{nickname}>\033[0m: {message}'
        print(formatted_message)

# Main function
def main():
    if len(sys.argv) < 5 or '-tls' not in sys.argv:
        display_help()
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    nickname = sys.argv[3]
    channel = sys.argv[4]

    if len(sys.argv) >= 7:
        account = sys.argv[5]
        password = sys.argv[6]
    else:
        account = None
        password = None

    irc_socket = connect_to_server(host, port, nickname, channel, account, password)

    receive_thread = threading.Thread(target=receive_messages, args=(irc_socket, channel, nickname))
    input_thread = threading.Thread(target=send_input, args=(irc_socket, channel, nickname))
    receive_thread.start()
    input_thread.start()
    receive_thread.join()
    input_thread.join()
    irc_socket.send(f'QUIT\r\n'.encode())
    irc_socket.close()

if __name__ == "__main__":
    main()

