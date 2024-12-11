# Networking Bonus Assignment
#       Author: Isaiah Stewart
#       Credit: Sample TCP Server code from Dr. Erdin
# Purpose: This program implements a client that communicates using TCP and connects to a server to play
#          a real-time rock, paper, scissors game hosted on the server


from socket import socket, AF_INET, SOCK_STREAM                             # For the socket programming functionality

running = False                               # Variable to signal the state of the client connection to the server
userInput = ''                                # Variable to store the client input

def Tcp_Client(server_ip, server_port):       # Function to facilitate communication with the server

    global running                            # References the global running signal
    global userInput                          # References the global input variable
    try:                                      # Attempt to create the connection

        client_socket = socket(AF_INET, SOCK_STREAM)                        # Creates a socket (socket()) using IPv4 (AF_INET) over TCP (SOCK_STREAM)
        client_socket.connect((server_ip, server_port))                     # Connects via the socket to the server socket
        running = True                        # If the connection was successful, the client is running (active)
        print('Connected to the server.')     # Report success


        while running:                        # While connected

            server_Message = client_socket.recv(1024).decode()              # Receive message from server
            print(server_Message)             # Print the message for the client


            if 'Enter input' in server_Message:                             # If the message contains 'Enter input'

                userInput = input('\n').strip().lower()                     # Get userInput
                client_socket.send(userInput.encode())                      # Send client message to server
            elif 'Waiting for player two. . .' in server_Message \
                    or 'Still waiting. . .' in server_Message:              # Else if client is waiting

                userInput = input('\n').strip().lower()                     # Get userInput
                while len(userInput) == 0:    # While the message is empty

                    userInput = input('\n').strip().lower()                 # Get userInput
                client_socket.send(userInput.encode())                      # Send client message to server
            elif 'Play again? (Y/N):' in server_Message:                    # Else if server is asking client if they want to 'Play again?'

                userInput = input('\n').strip().lower()                     # Get userInput
                while len(userInput) == 0:    # While the message is empty

                    userInput = input("\n").strip().lower()                 # Get userInput
                client_socket.send(userInput.encode())                      # Send client message to server
            elif 'Timed-out' in server_Message:                             # Else if client 'Timed-out'

                userInput = input('\nYou timed-out. Would you like to '     
                                  'reconnect? : \n').strip().lower()        # Get userInput with prompt informing them they timed-out for quick-reconnect
                while len(userInput) == 0:    # While the message is empty

                    userInput = input('\n').strip().lower()                 # Get userInput
                if userInput == 'yes' or userInput == 'y':                  # If client wants to reconnect

                    client_socket.close()     # Close timed-out connection
                    try:                      # Attempt to reconnect

                        client_socket = socket(AF_INET, SOCK_STREAM)        # Create new socket for client
                        client_socket.connect((server_ip, server_port))     # Attempt to connect to the server socket from new client socket
                    except WindowsError as err:                             # If there was an error reconnecting to the server

                        print('\nThere was an error '
                              'reconnecting to the server\n: ', err)        # Inform client about the error
                else:                         # Else if client does not want to reconnect

                    print('\nClosing connection. . .\n')                    # Inform client the connection is being closed
                    running = False           # Client is no longer running
            if userInput == 'close connection':                             # If client wants to close their connection with the server

                print('\nClosing connection. . .\n')                        # Inform client the connection is being closed
                running = False

        client_socket.close()                 # When running is no longer true close the connection
        print('Connection closed.')           # Inform client the connection has been closed
    except OSError as err:                    # If the error is likely related to the socket connection
                                              # (We use OSError instead of WindowsError because the client might be from a different OS
        print('There was an error connecting to the server - '
              '(Did you enter IP and Port # correctly?): ', err)            # Inform client of error
    except RuntimeError as err:               # If there was an error during the communication with the server

        print('An error occurred: ', err)     # Inform client of the error and show the error
def clientEntry():                            # Ask for server information and enter client function

    server_ip = str(input('\nWhat is the '
                          'IP address of the server? : \n'))                # Stores the IP address of the server
    server_port = int(input('\nWhat is the port number '
                            'the server is listening on? : \n'))            # Stores the port number of the server

    Tcp_Client(server_ip, server_port)        # Run the client function to connect to the server and communicate



clientEntry()                                 # Run the entry function