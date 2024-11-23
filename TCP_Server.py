# Networking Bonus Assignment
#       Author: Isaiah Stewart
#       Credit: Sample TCP Server code from Dr. Erdin
# Purpose: This program implements a server that communicates using TCP and listens for connections
#          over a certain port, and hosts a real-time rock, paper, scissors game with match history

# Import relevant libraries
from socket import *
import threading
from threading import Lock, Event
import random


running = False         # Global variable for server status
threads = []            # Global variable for clients
inputs = {}             # Global variable for realtime inputs
ready = Event()         # Event to signal the readiness of both players
lock = Lock()           # Locks the threads so one threads adds inputs at a time
clients = {}            # stores client information (connection, address)

def createServer():                           # Server creation function

    global running                            # References the server status to be updated
    global threads                            # References the global threads list

    try:                                      # Attempts to create server

        maxNumOfPlayers = 2                   # Server will allow up to this many connections (clients/players) for the game
        serverPort = 12000                    # Server will listen for connections on this port
        serverSocket = socket(AF_INET,
                              SOCK_STREAM)    # Creates a socket (socket()) using IPv4 (AF_INET) over TCP (SOCK_STREAM)
        serverSocket.bind(('', serverPort))
        serverSocket.listen(maxNumOfPlayers)  # Server will listen for new connections until max is reached, then server will deny new connections
        running = True                        # If previous statements were successful, server is running
        print('The server is available.\n\n') # Server is up
    except RuntimeError:

        return ValueError('Server creation failed. . .')                # Catches server creation failure


    while running:                                                      # While server is running

        connection, address = serverSocket.accept()                     # Accept new connections
        print("Connection from: " + str(address))                       # Outputs the IP of the connecting client

        client_Thread = threading.Thread(target = client,
                                         args = (connection, address))  # Makes individual threads for client sessions
        client_Thread.address = address                                 # The thread will now store the address of the corresponding client
        client_Thread.connection = connection                           # The thread will now store the connection of the corresponding client
        client_Thread.start()                                           # Starts the client session
        threads.append(client_Thread)                                   # Stores the active session

        for thread in threads:                                          # iterates through the sessions
            if not thread.is_alive():                                   # if session is no longer active
                threads.remove(thread)                                  # remove the session from the list

    print('Shutting down the server. . .')                              # When the server is no longer running
    for thread in threads:                                              # iterates through the sessions
        thread.join()                                                   # Waits for threads to finish

    serverSocket.close()                                                # Closes the server socket
def client(connection, address):

    global clients
    wins = 0                                                            # Keeps track of wins for the client
    losses = 0                                                          # Keeps track of client losses
    ties = 0                                                            # Keeps track of client ties
    clients[threading.current_thread()] = (connection, address)         # Maps threads to their connection
    connection.settimeout(30)                                           # The thread will wait for 30 seconds for the user to enter their input
    message = 'This is a real-time rock, paper, scissors game.\n' \
              'Please enter your input as either rock, paper, scissors,\n' \
              'or 1-3 respectively whenever you are ready.\n' \
              '(Enter (two player) if you want to play with another player.\n' \
              '(P.S. - If you take longer than 30 secs the server will\n' \
              'drop your connection. - Or enter (close connection))'

    connection.send(message.encode())
    try:                                                                # Attempts to execute the game

        while True:                                                     # Continue until game is over or client times-out or ends the session

            robotChoice = str(random.randint(1, 3))                     # robot will choose either rock, paper, or scissors (1-3) as a string
            try:

                connection.send('Enter input\n'.encode())
                userInput = connection.recv(1024).decode().strip().lower# Receive userInput
            except RuntimeError:                                        # Client did not enter data
                print('Timeout - client: ' + str(address)               # Report which user timed-out
                      + ' failed to enter data.')                       # Print error
                break                                                   # Exit loop

            if userInput == 'close connection':                         # Client wants to close the connection
                print('Closing connection with client: '                # Close connection
                      + str(address))                                   # Client closed connection
                break                                                   # Exit loop

            if userInput == 'two player':                               # Client wants to play two player
                twoPlayer = True                                        # Two player
                opponent = threads[1].address
            else:                                                       # Client does not want to play two player
                twoPlayer = False                                       # Not Two player
                opponent = 'robot'
            if not twoPlayer:
                message, wins, losses, ties = robot(userInput, robotChoice,
                                                    message, ties, wins, losses,
                                                    opponent, address, connection)
            else:
                realtime(connection, address)
                break

            connection.send(message.encode())

    except RuntimeError as err:

        print('Error: ' + str(err) + 'with client: ' + str(address))
def robot(userInput, robotChoice, message, ties, wins, losses, opponent, address, connection):
    if userInput == '1' or userInput == 'rock':
        if robotChoice == '1':
            message = 'Robot threw rock, tie!'
            ties += 1
        elif robotChoice == '2':
            message = 'Robot threw paper, ouch!'
            losses += 1
        elif robotChoice == '3':
            message = 'Robot threw scissors, you win!'
            wins += 1
    if userInput == '2' or userInput == 'paper':
        if robotChoice == '1':
            message = 'Robot threw rock, you win!'
            wins += 1
        elif robotChoice == '2':
            message = 'Robot threw paper, tie!'
            ties += 1
        elif robotChoice == '3':
            message = 'Robot threw scissors, ouch!'
            losses += 1
    if userInput == '3' or userInput == 'scissors':
        if robotChoice == '1':
            message = 'Robot threw rock, ouch!'
            losses += 1
        elif robotChoice == '2':
            message = 'Robot threw paper, you win!'
            wins += 1
        elif robotChoice == '3':
            message = 'Robot threw scissors, tie!'
            ties += 1

        connection.send(message.encode())
        message = '\tStats: \n' \
                  'Player:\t\t' + str(address) + '\n' \
                  'Opponent:\t\t' + str(opponent) + '\n' \
                  'Wins:\t\t' + str(wins) + '\n' \
                  'Ties:\t\t' + str(ties) + '\n' \
                  'Losses:\t\t' + str(losses) + '\n'

        with open('stats.txt', 'w') as file:
            file.write(message)
        connection.send(message.encode())
    return [message, wins, losses, ties]
def realtime(connection, address):

    global inputs
    global ready
    global lock

    player_ID = address         # identifier for the player


    if len(threads) < 2:                                                    # There are not yet two clients
        connection.send('Waiting for player two. . .\n'.encode())           # Inform user the server is waiting for another player to match them
        while len(threads) < 2:                                             # Wait for other player. . .
            ready.wait(1)                                                   # Check every second

    playerTwo = next(thread for thread in threads if thread.address != address)     #
    playerTwo_ID = playerTwo.address                                                # identifier for the opponent

    while True:

        try:

            ties = 0
            playerOneWins = 0
            playerTwoWins = 0

            connection.send('Enter input\n'.encode())
            playerInput = connection.recv(1024).decode().strip.lower()

            valid_Choices = ['rock', 'paper', 'scissors', '1', '2', '3']
            if playerInput not in valid_Choices:
                connection.send("Invalid choice. Try again.\n".encode())
                continue

            with lock:
                inputs[player_ID] = playerInput
                if len(inputs) == 2:
                    ready.set()

            connection.send('Waiting for opponent. . .\n'.encode())
            ready.wait()

            with lock:
                if len(inputs) == 2:
                    playerOneInput = inputs[player_ID]
                    playerTwoInput = inputs[playerTwo_ID]

                    result = determine_Winner(playerOneInput, playerTwoInput)

                    if result == 'tie':
                        ties += 1
                    elif result == 'player one':
                        playerOneWins += 1
                    else:
                        playerTwoWins += 1

                    connection.send(result.encode())
                    clients[playerTwo].send(result.encode())


                    inputs.clear()
                    ready.clear()

            with open('stats.txt', 'w') as file:
                file.write('Player ' + str(address) + ' Wins: ' + str(playerOneWins) + '\tLosses: ' + str(playerTwoWins) + '\n')

            connection.send('Play again? (Y/N):\n'.encode())
            player_Response = connection.recv(1024).decode().strip().lower()

            if player_Response != 'y' or player_Response != 'yes':
                connection.send('Game over.\n'.encode())
                break

        except RuntimeError as err:
            print('Error during realtime game with client: ' + str(player_ID) + str(err))
            break

        finally:
            connection.close()
def determine_Winner(playerOne_Input, playerTwo_Input):

    if playerOne_Input == 'rock':
        playerOne_Input = '1'
    if playerOne_Input == 'paper':
        playerOne_Input = '2'
    if playerOne_Input == 'scissors':
        playerOne_Input = '3'
    if playerTwo_Input == 'rock':
        playerOne_Input = '1'
    if playerTwo_Input == 'paper':
        playerOne_Input = '2'
    if playerTwo_Input == 'scissors':
        playerOne_Input = '3'

    if playerOne_Input == playerTwo_Input:
        result = 'tie'
    elif playerOne_Input == '1' and playerTwo_Input == '3':
        result = 'player one'
    elif playerTwo_Input == '1' and playerTwo_Input == '3':
        result = 'player two;'
    elif int(playerOne_Input) >  int(playerTwo_Input):
        result = 'player one'
    else:
        result = 'player two'

    return result
def serverEntry():

    print('Creating server. . .\n\n')

    try:
        server_Thread = threading.Thread(target = createServer)
        server_Thread.start()

        server_Thread.join()
    except ValueError as err:
        print('Error: ', err)

serverEntry()