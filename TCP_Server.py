# Networking Bonus Assignment
#       Author: Isaiah Stewart
#       Credit: Sample TCP Server code from Dr. Erdin
# Purpose: This program implements a server that communicates using TCP and listens for connections
#          over a certain port, and hosts a real-time rock, paper, scissors game with match history

# Import relevant libraries
from socket import *                          # For the socket programming
import threading                              # For handling TCP client threads
from threading import Lock, Event             # To help synchronize the clients for the real-time game
import time                                   # Helps in the realtime function and in the server creation and timeout functionality
import random                                 # To generate robot choices for the robot game

running = False                               # Global variable for server status
threads = []                                  # Global variable for clients
inputs = {}                                   # Global variable for realtime inputs
ready = Event()                               # Event to signal the readiness of both players
lock = Lock()                                 # Locks the threads so one thread adds inputs at a time
realTimePlayers = 0                           # Keeps track of how many players are in realtime function
robotResult = ''                              # Stores the result from the robot random choice generator
opponent = ''                                 # Stores the type of opponent (robot/player)
playerOne_Input = ''                          # Stores the choice (rock, paper, scissors) of the first player
playerTwo_Input = ''                          # Stores the choice (rock, paper, scissors) of the second player
serverSocket = None                           # Stores the serverSocket information
responses = []                                # Stores the responses from both players
updated = False                               # Stores the state of the match history file
playerTwo = None                              # Placeholder for playerTwo connection
playerTwo_ID = None                           # Placeholder for playerTwo address
playerOne = None                              # Placeholder for playerOne connection
playerOne_ID = None                           # Placeholder for playerOne address
lastActivity = None                           # Keeps track of the time of the last client interaction


def createServer():                           # Server creation function

    global running                            # References the global server status to be updated
    global threads                            # References the global threads list
    global serverSocket                       # References the global variable that stores the serverSocket information
    global lastActivity                       # References the global lastActivity information
    serverTimeoutTime = 300                   # Stores the time the server stays available after lastActivity


    try:                                      # Attempts to create and run server

        maxNumOfPlayers = 5                   # Server will allow up to this many connections (clients/players) for the game
        serverPort = 26000                    # Server will listen for connections on this port
        serverSocket = socket(AF_INET,
                              SOCK_STREAM)    # Creates a socket (socket()) using IPv4 (AF_INET) over TCP (SOCK_STREAM)
        serverSocket.bind(('', serverPort))   # Binds the serverSocket to the port assigned to serverPort
        serverSocket.listen(maxNumOfPlayers)  # Server will listen for new connections until max is reached, then server will deny new connections
        running = True                        # If previous statements were successful, server is running
        print('The server is available.\n\n') # Server is up

        lastActivity = time.time()            # Set lastActivity baseline

        while running:                        # While server is running

            serverSocket.settimeout(5)        # Server will check every five seconds for new connections

            try:                              # Attempt to find new connection requests

                connection, address = serverSocket.accept()                 # Accept new connections
                print("Connection from: " + str(address))                   # Logs the IP of the connecting client
                lastActivity = time.time()    # Update lastActivity timestamp

                client_Thread = threading.Thread(
                    target=client, args=(connection, address))              # Makes individual threads for client sessions
                client_Thread.address = address                             # The thread will now store the address of the corresponding client
                client_Thread.connection = connection                       # The thread will now store the connection of the corresponding client
                client_Thread.start()                                       # Starts the client session
                threads.append(client_Thread) # Stores the active session
            except TimeoutError:              # After timeout (Five seconds have passed)

                pass                          # Recheck (Go back to loop)
            for thread in threads[:]:         # Makes a copy of the threads list and iterates through
                                              # (Actively iterating through a list you are modifying is poor practice)

                if not thread.is_alive():     # If session is no longer active

                    threads.remove(thread)    # Remove the session from the list
                else:                         # Else (the session is active)
                    lastActivity = time.time()                              # Update the lastActivity value
            if len(threads) == 0 and \
                    (time.time() - lastActivity >= serverTimeoutTime):      # If there are no active threads and serverTimeoutTime has been exceeded

                print('Inactive server: '
                      'No activity for five minutes - Shutting down. . .')  # Log inactivity and shut-down
                running = False               # Stop running

        serverSocket.close()                  # Free up serverSocket
    except WindowsError:                      # If server creation fails

        print('Server creation failed. . . '
              '(Port Already in Use?)')       # Catches server creation failure and provides debugging info
    except Exception as err:                  # If there is some other error

        print('Error in createServer: ', err) # Log error
        print('Attempting shut-down. . .')    # Log shut-down attempt
        unexpectedExit(serverSocket)          # Attempt
def unexpectedExit(sSocket):

    global threads                            # References the global threads list

    if len(threads) > 0:                      # If there are active threads

        for thread in threads[:]:             # Makes a copy of the active threads and iterates through them

            try:                              # Attempts to close the connection

                thread.connection.close()     # Close the connection
            except Exception as err:          # If there was an error closing the connection

                print('Error closing client '
                      'connection: ' + str(thread.address), err)            # Log error
        for thread in threads:                # Iterate through the threads

            thread.join()                     # Wait for threads to finish
        try:                                  # Attempt to close the serverSocket

            sSocket.close()              # Close the serverSocket
            print("Server socket closed.")    # Log the closing
        except Exception as err:              # If there was an error closing the server

            print('Error closing server socket: ', err)                     # Log error
def client(connection, address):              # Client function to handle client threads

    global realTimePlayers                    # References the global realTimePlayers variable
    global opponent                           # References the global opponent variable
    stats = {                                 # Stores the stats for the client (wins, ties, losses)

        'Wins': 0,
        'Ties': 0,
        'Losses': 0
    }


    connection.settimeout(30)                 # The thread will wait for 30 seconds for the user to enter their input
    message = 'This is a real-time rock, paper, scissors game.\n' \
              'Please enter your input as either rock, paper, scissors,\n' \
              'or 1-3 respectively whenever you are ready.\n' \
              '(Enter (two player) if you want to play with another player.\n' \
              '(P.S. - If you take longer than 30 secs the server will\n' \
              'drop your connection. - Or enter (close connection))'        # Intro-message for new players
    connection.send(message.encode())         # Send intro-message

    try:                                      # Attempts to execute the game

        while True:                           # Continue until game is over or client times-out or ends the session

            robotChoice = str(random.randint(1, 3))                         # robot will choose either rock, paper, or scissors (1-3) as a string
            try:                              # Attempts to receive input from player

                connection.send('\nEnter input\n'.encode())                 # Prompts input from player
                userInput = connection.recv(1024).decode().strip().lower()  # Receive userInput
            except TimeoutError:                                            # If client did not enter data

                print('Timeout - client: ' + str(address[0])                # Report which user timed-out
                      + ' failed to enter data.')                           # Print error
                connection.send('\nTimed-out\n'.encode())                   # Inform client they timed-out
                break                                                       # Exit loop
            if userInput == 'close connection':                             # If client wants to close the connection

                print('Closing connection with client: '
                      + str(address))                                       # Server logging information
                break                                                       # Exit loop
            if userInput == 'two player':                                   # If client wants to play two player

                twoPlayer = True                                            # Set twoPlayer flag for client handling function
            else:                                                           # Else if player does not want to play twoPlayer

                twoPlayer = False                                           # Set twoPlayer flag
                opponent = 'robot'                                          # Player is not playing twoPlayer, so they are playing against the bot
            if not twoPlayer:                                               # If player is not playing twoPlayer

                robot(userInput, robotChoice, stats, address, connection)   # Send player to robot function
            else:                                                           # If twoPlayer is true

                if realTimePlayers == 2:      # If there are already two players in twoPlayer

                    connection.send('\nTwo player '
                                    'is full, sorry!\n'.encode())           # Inform client twoPlayer is full
                else:                         # Else if twoPlayer is not full

                    realTimePlayers += 1                                    # Increment realTimePlayers variable
                    realtime(connection, address)                           # Send player to realtime function
                    connection.settimeout(30) # Reset player's timeout value
                    connection.send(message.encode())                       # Resend intro-message to player to let them know they are back to client-handling function
    except Exception as err:                                                # If any errors occur in the instance of the client handling function

        print('Error: ' + str(err) + ' with client: ' + str(address))       # Log the error and the client associated with it
def robot(userInput, robotChoice, stats, address, connection):              # Function for a player to play against a robot

    global robotResult                        # References the global robotResult
    global updated                            # References the global updated status
    statsFile = 'stats.txt'                   # Stores the name of the match history file
    client_IP = str(address[0])               # Stores the client's IP address obtained from the first part of the address
    lines = []                                # Stores the lines from the match history file


    try:                                      # Attempts to open the match history file

        with open(statsFile, 'r') as file:    # Open the stats file in reading mode

            lines = file.readlines()          # Reads in all the lines from the file and stores them in the lines list
        for i in range(len(lines)):           # Increment through each line in the file

            playerLine = lines[i].strip()     # Stores each line without leading and trailing whitespace for processing

                                              # Assigns the stored stats in the client function to the stored stats for the connected client
            if ("Player:\t\t" + client_IP) in playerLine:                   # If the line contains the client IP

                stats['Wins'] = \
                    int(lines[i + 2].strip().split(':')[1].strip())         # Player's previous wins are recovered from the file
                stats['Ties'] = \
                    int(lines[i + 3].strip().split(':')[1].strip())         # Player's previous ties are recovered from the file
                stats['Losses'] = \
                    int(lines[i + 4].strip().split(':')[1].strip())         # Player's previous losses are covered from the file
                updated = True                                              # Sets the updated flag for the match history file
                break                         # Exits the for loop - match history is now updated
    except FileNotFoundError:                 # If the file is not found
        print('\nPotential error locating match history file.\n')           # Possible error, or could file has not yet been created

    if userInput == '1' or userInput == 'rock':                             # If player enters rock

        if robotChoice == '1':                                              # And if robot chose rock

            robotResult = 'Robot threw rock, tie!'                          # Assign result
            stats['Ties'] += 1                                              # Update player stats
        elif robotChoice == '2':                                            # And if robot chose paper

            robotResult = 'Robot threw paper, ouch!'                        # Assign result
            stats['Losses'] += 1                                            # Update stats
        elif robotChoice == '3':                                            # And if robot chose scissors

            robotResult = 'Robot threw scissors, you win!'                  # Assign result
            stats['Wins'] += 1                                              # Update stats
    elif userInput == '2' or userInput == 'paper':                          # If player enters paper

        if robotChoice == '1':                                              # And if robot chose rock

            robotResult = 'Robot threw rock, you win!'                      # Assign result
            stats['Wins'] += 1                                              # Update stats
        elif robotChoice == '2':                                            # And if robot paper

            robotResult = 'Robot threw paper, tie!'                         # Assign result
            stats['Ties'] += 1                                              # Update stats
        elif robotChoice == '3':                                            # And if robot chose scissors

            robotResult = 'Robot threw scissors, ouch!'                     # Assign result
            stats['Losses'] += 1                                            # Update stats
    elif userInput == '3' or userInput == 'scissors':                       # If player enters scissors

        if robotChoice == '1':                                              # And if robot chose rock

            robotResult = 'Robot threw rock, ouch!'                         # Assign result
            stats['Losses'] += 1                                            # Update stats
        elif robotChoice == '2':                                            # And if robot chose paper

            robotResult = 'Robot threw paper, you win!'                     # Assign result
            stats['Wins'] += 1                                              # Update stats
        elif robotChoice == '3':                                            # And if robot chose scissors

            robotResult = 'Robot threw scissors, tie!'                      # Assign result
            stats['Ties'] += 1                                              # Update stats
    else:                                                                   # If none of the previous checks match user input, there is an error
        robotResult = 'Error: Invalid input.'                               # Inform player their input is invalid (Assign result)
    connection.send(robotResult.encode())                                   # Send result to player

    message = '\n\tStats: \n' \
              'Player:\t\t' + str(address[0]) + '\n' \
              'Opponent:\t\t' + str(opponent) + '\n' \
              'Wins:\t\t' + str(stats['Wins']) + '\n' \
              'Ties:\t\t' + str(stats['Ties']) + '\n' \
              'Losses:\t\t' + str(stats['Losses']) + '\n'                   # Store stats information in a message for the player
    connection.send(message.encode())         # Send message to player

    with open(statsFile, 'w'):                # Open the match history file in writing mode

        for i in range(len(lines)):           # Iterate through each line in the file

            playerLine = lines[i].strip()     # Store the current line
            if ("Player:\t\t" + client_IP) in playerLine:                   # If the line has the player IP

                lines[i + 2] = 'Wins:\t\t' + str(stats['Wins']) + '\n'      # Player's previous wins are updated
                lines[i + 3] = 'Ties:\t\t' + str(stats['Ties']) + '\n'      # Player's previous ties are updated
                lines[i + 4] = 'Losses:\t\t' + str(stats['Losses']) + '\n'  # Player's previous losses are updated
                updated = True                # The stats have been updated
                break                         # Break out of the for loop, stats have been updated
        if not updated:                       # If the player IP was not found, and thus the stats file was not updated:
            newEntry = '\n\tStats: \n' \
                       'Player:\t\t' + str(address[0]) + '\n' \
                       'Opponent:\t\t' + str(opponent) + '\n' \
                       'Wins:\t\t' + str(stats['Wins']) + '\n' \
                       'Ties:\t\t' + str(stats['Ties']) + '\n' \
                       'Losses:\t\t' + str(stats['Losses']) + '\n'          # Create new entry for the file
            lines.append(newEntry)            # Append new entry to the file
        with open(statsFile, 'w') as file:    # Open the file in writing mode
            file.truncate(0)                  # Delete contents
            file.writelines(lines)            # Rewrite contents (may help with duplicate entries)
def realtime(connection, address):            # Function for two player game

    global inputs                             # References the global player inputs variable
    global ready                              # References the global ready signal
    global lock                               # References the global thread lock
    global playerOne_Input                    # References the global variable that stores the input from the first player
    global playerTwo_Input                    # References the global variable that stores the input from the second player
    global responses                          # References the global variable that stores the player responses
    global realTimePlayers                    # References the global realTimePlayers variable
    global playerTwo                          # References the global playerTwo variable (stores connection)
    global playerTwo_ID                       # References the global playerTwo_ID variable (stores address)
    global playerOne                          # References the global playerOne variable (stores connection)
    global playerOne_ID                       # References the global playerOne_ID variable (stores address)
    ties = 0                                  # Stores the ties from the game session
    playerOneWins = 0                         # Stores the wins of playerOne
    playerTwoWins = 0                         # Stores the wins of playerTwo
    player_ID = address                       # Identifier for instance player (could be playerOne or playerTwo)


    if realTimePlayers < 2:                   # If there are not yet two clients

        connection.send('\nWelcome player one!\n'.encode())                 # Send welcome message to playerOne
        connection.send('Waiting for player two. . .\n'
                        '(You may leave the waiting queue\n'
                        'at any time by typing (Exit)\n'.encode())          # Inform user the server is waiting for another player to match them


        while realTimePlayers < 2:            # While there are not two players for twoPlayer

            try:                              # Check for player input and check if player wants to exit twoPlayer

                connection.settimeout(1)      # Check every second
                message = connection.recv(1024).decode().strip().lower()    # Receive message if there is one
                if message == 'exit':         # If player wants to leave the queue

                    connection.send('\nExiting the waiting '                
                                    'queue. . . \n'.encode())               # Inform player they are leaving the game
                    realTimePlayers -= 1      # Decrement realTimePlayers
                    inputs.clear()            # Clear inputs list
                    ready.clear()             # Clear ready signal
                    return                    # Return player to client handling function
                else:

                    connection.send('\nStill waiting. . . '
                                    '(Enter exit to exit queue)'
                                    '\n'.encode())                          # Inform player they are still waiting
            except TimeoutError:              # Timeout is expected while waiting (no player input)

                pass                          # Continue looping
        connection.settimeout(30)             # Reset player time-out value
        playerOne = connection                # Assign playerOne connection
        playerOne_ID = address                # Assign playerOne address
        for thread in threads:                # Iterate through active threads
            if thread.connection != connection:                             # Ensure it's not the same connection
                playerTwo = thread.connection                               # Assigns the playerTwo connection
                playerTwo_ID = thread.address                               # Identifier for the playerTwo
                break                         # playerTwo identified, exit for loop
        playerTwo.send('\nWelcome player two!\n'.encode())                  # Send the welcome message to the second player
    while True:                               # Continue as long as the session is still going

        try:                                  # Attempt to send prompts to players, receive input, and synchronize the client threads


            ready.wait(1)                     # Wait for playerOne to catch up (playerOne checks for playerTwo every second)
            connection.settimeout(30)         # Ensure time-out value is set to 30 seconds for players
            connection.send('Enter input\n'.encode())                       # Send both players the input prompt
            try:                              # Attempt to receive players' input

                playerInput = \
                    connection.recv(1024).decode().strip().lower()          # Receive players' input
                while len(playerInput) == 0:  # While playerInput is empty

                    ready.wait(2)             # Wait two second
                    connection.send('Enter input\n'.encode())               # Resend player the input prompt
                    playerInput = \
                        connection.recv(1024).decode().strip().lower()      # Reassign playerInput
            except TimeoutError:              # If a player fails to enter input in time

                print('Timeout - client: ' + str(address[0])                # Report which player timed-out
                      + ' failed to enter data.')                           # Print error
                connection.send('\nTimed-out\n'.encode())                   # Inform player they timed out
                realTimePlayers -= 1          # Decrement realTimePlayers
                inputs.clear()                # Clear player inputs
                ready.clear()                 # Clear ready signal
                return                        # Return player to client handling function
            except WindowsError:              # If client closes their connection via 'Close connection'

                print('Client: ' + str(address[0]) +
                      ' closed their connection to the server.')            # Log client disconnect
                realTimePlayers -= 1          # Decrement the numbers of players
                inputs.clear()                # Clear player inputs
                ready.clear()                 # Clear ready signal
                return                        # Exit the twoPlayer function
            valid_Choices = ['rock', 'paper', 'scissors', '1', '2', '3']    # List for types of valid input
            while playerInput not in valid_Choices:                         # If the input entered by the player does not match any valid inputs

                connection.send('Invalid choice. Try again.\n'.encode())    # Inform player their input was invalid
                connection.send('Enter input\n'.encode())                   # Send player the input prompt
                try:                          # Attempt to receive player's input

                    playerInput = \
                        connection.recv(1024).decode().strip().lower()      # Receive player's input
                except TimeoutError:          # If a player fails to enter input in time

                    print('Timeout - client: ' + str(address[0])            # Report which player timed-out
                          + ' failed to enter data.')                       # Print error
                    connection.send('\nTimed-out\n'.encode())               # Inform player they timed out
                    realTimePlayers -= 1      # Decrement realTimePlayers
                    inputs.clear()            # Clear player inputs
                    ready.clear()             # Clear ready signal
                    return                    # Return player to client handling function
            with lock:                        # Limit following code to one client thread at a time

                inputs[player_ID] = playerInput                             # Assign player input
                if len(inputs) == 2:          # If both players have entered their input

                    ready.set()               # We can move on
            connection.send('\nWaiting for opponent. . .\n'.encode())       # Inform the first player the other player is still entering input
            start_time = time.time()          # Get base-line time
            while not ready.is_set():         # While ready flag is not set

                if time.time() - start_time >= 30:                          # If the player has waited longer than the normal time-out value

                    connection.send('Other player failed to respond, or '
                                    'encountered some error: '
                                    'Exiting game. . .'.encode())           # Inform player the other player encountered trouble
                    inputs.clear()            # Clear inputs to clean-up
                    ready.clear()             # Clear ready flag
                    realTimePlayers -= 1      # Decrement realTimePlayers
                    return                    # Return player to client-handling function
                if realTimePlayers == 1:      # If the other player is no longer playing

                    connection.send('\nOpponent may have disconnected '
                                    'or timed-out. Exiting game. . .'
                                    '\n'.encode())                          # Inform the first player that the other player
                                                                            # may have timed-out or had some error
                    inputs.clear()            # Clear the inputs
                    ready.clear()             # Clear the ready signal
                    realTimePlayers -= 1      # Decrement realTimePlayers
                    return                    # Return the player to the client handling function
                ready.wait(1)                 # Recheck after one second
            responses.clear()                 # Clears residual responses from previous session
            connection.settimeout(30)         # Reset player time-out value
            connection.send('\nOpponent input received\n'.encode())         # Inform player the other player responded
            with lock:                        # Limit following code to one client thread at a time

                playerOne_Input = inputs[playerOne_ID]                      # Assign playerOne input
                playerTwo_Input = inputs[playerTwo_ID]                      # Assign playerTwo input

                print('Player ID: ' + str(player_ID) + '\t1Input: '
                      + str(playerOne_Input) + '\t2Input: '
                      + str(playerTwo_Input))                               # Log determination
                result = determine_Winner()   # Determine the winner based on playerInputs

                if result == 'tie':           # If the result is a tie

                    ties += 1                 # Increment ties
                elif result == 'player one':  # Else if the result is a win for playerOne

                    playerOneWins += 1        # Increment playerOneWins
                else:                         # Else if the result does not match previous conditions

                    playerTwoWins += 1        # That means the result is a win for playerTwo

                if result == 'tie':           # If it was a tie

                    result = 'tie!'           # Reassign result with an exclamation mark (I was lazy)
                else:                         # Else if it isn't a tie

                    result = result + ' wins!'                              # Prepare the result to send to the players
                connection.send(result.encode())                            # Send result to both players
            connection.send('\nPlay again? (Y/N):\n'.encode())              # Ask players if they want to continue playing

            try:                              # Attempt to receive player responses

                player_Response = \
                    connection.recv(1024).decode().strip().lower()          # Receive player response
                with lock:                    # Limit one client thread at a time to modify the following code

                    responses.append(player_Response)                       # Add player response to the responses list
            except TimeoutError:              # If a player failed to respond

                print('Timeout - client: ' + str(address[0])
                      + ' failed to enter data.')                           # Log which user timed-out
                connection.send('\nOne of the players '
                                'declined to play again.\n'.encode())       # Send message to both players
                responses.append('no')        # Player declined to play again or otherwise failed to say yes
                inputs.clear()                # Clear inputs to clean-up
                ready.clear()                 # Clear ready flag to clean-up
                realTimePlayers -= 1          # Decrement realTimePlayers
                return                        # Return player to client-handling function
            if len(responses) < 2:            # If both players have not yet responded

                connection.send('\nWaiting for other '
                                'player to respond. . .\n'.encode())        # Inform player the other player is still deciding
                start_time = time.time()      # Keep track of how longer the player is waiting

                while len(responses) < 2:     # While there are still not two responses
                    if time.time() - start_time >= 30:                      # If the player has waited longer than the normal time-out value

                        connection.send('Other player failed to respond, or '
                                        'encountered some error: '
                                        'Exiting game. . .'.encode())       # Inform player the other player encountered trouble
                        inputs.clear()        # Clear inputs to clean-up
                        ready.clear()         # Clear ready flag
                        realTimePlayers -= 1  # Decrement realTimePlayers
                        return                # Return player to client-handling function

                    ready.wait(1)             # Recheck after one second
            for response in responses:        # Check both players' response

                if response != 'y' and response != 'yes':                   # If the response is not yes

                    connection.send('\nOne of the players declined to '     
                                    'play again, game over.\n'.encode())    # Inform both players the game is over
                    connection.send(('Stats:\n' +
                                     'Player ' + str(address) + ' Wins: '
                                    + str(playerOneWins) + '\tLosses: '
                                     + str(playerTwoWins) + '\n').encode()) # Send session stats to players
                    realTimePlayers -= 1      # Decrement realTimePlayers
                    inputs.clear()            # Clear the inputs
                    ready.clear()             # Clear the ready signal
                    return                    # Return active players to client handling function
            connection.send('\nBoth players '
                            'accepted the rematch.\n'.encode())             # If both players accepted: inform players
            inputs.clear()                    # Clear the inputs
            ready.clear()                     # Clear the ready signal
        except Exception as err:              # If any error occurs outside the previous try blocks

            print('Unexpected error during realtime '
                  'game with client: ' + str(player_ID) + ': ', err)         # Log error
            realTimePlayers -= 1              # Decrement realtime players
            inputs.clear()                    # Clear the inputs
            ready.clear()                     # Clear the ready signal
            return                            # Exit function
def determine_Winner():                       # Function to determine the winner of the twoPlayer interaction

    global playerOne_Input                    # References the global variable storing playerOne's input
    global playerTwo_Input                    # References the global variable storing playerTwo's input
    inputOne = playerOne_Input                # Store playerOne's input in a local variable
    inputTwo = playerTwo_Input                # Store playerTwo's input in a local variable

    if inputOne == 'rock':                    # Check if input needs converted

        inputOne = '1'                        # Convert input for processing
    elif inputOne == 'paper':                 # Check if input needs converted

        inputOne = '2'                        # Convert input for processing
    elif inputOne == 'scissors':              # Check if input needs converted

        inputOne = '3'                        # Convert input for processing
    if inputTwo == 'rock':                    # Check if input needs converted

        inputTwo = '1'                        # Convert input for processing
    elif inputTwo == 'paper':                 # Check if input needs converted

        inputTwo = '2'                        # Convert input for processing
    elif inputTwo == 'scissors':              # Check if input needs converted

        inputTwo = '3'                        # Convert input for processing
    if inputOne == inputTwo:                  # Compare inputs

        result = 'tie'                        # Assign result
    elif inputOne == '1' and inputTwo == '3': # Compare inputs

        result = 'player one'                 # Assign result
    elif inputTwo == '1' and inputOne == '3': # Compare inputs

        result = 'player two'                 # Assign result
    elif int(inputOne) > int(inputTwo):       # Compare inputs

        result = 'player one'                 # Assign result
    else:                                     # Compare inputs

        result = 'player two'                 # Assign result

    try:                                      # Attempt to return result

        return result                         # Return result
    except Exception as err:                  # If there was an error returning the result

        print('Error with determine '
              'winner: ', err)                # Log error
        return                                # Exit function
def serverEntry():                            # Entry point function of program

    print('Creating server. . .\n\n')         # Log server creation

    try:                                      # Attempt to create server

        server_Thread = \
            threading.Thread(target = createServer)                         # Create server thread
        server_Thread.start()                 # Start server thread

        server_Thread.join()                  # Wait for server thread to finish
    except Exception as err:                  # If there was an error creating and starting server thread

        print('Error: ', err)                 # Log error

serverEntry()                                 # Enter program