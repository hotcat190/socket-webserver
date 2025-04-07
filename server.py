#import socket module
from socket import *
from threading import Lock, Thread
import sys # In order to terminate the program

connection_counter = 0
thread_lock = Lock()

#Prepare a sever socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # Reuse the address

serverName = '192.168.194.79'
serverPort = 12000
serverSocket.bind(('', serverPort))

# Create a list to keep track of threads
threads = []

class ClientThread(Thread):
    def __init__(self, connectionSocket, addr, lock):
        Thread.__init__(self)
        self.connectionSocket = connectionSocket
        self.addr = addr
        self.lock = lock
        print("New connection added: ", addr)

    def run(self):
        global connection_counter
        print("Connection from: ", self.addr)
        with self.lock:
            connection_counter += 1
            print("Active connections: ", connection_counter)

        try:
            message = self.connectionSocket.recv(1024).decode()
            print("Message received: ", message)
            filename = message.split()[1]
            print("Filename: ", filename)
            f = open(filename[1:])
            outputdata = f.readlines()

            #Send one HTTP header line into socket
            self.connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
            self.connectionSocket.send("\r\n".encode())  #Empty line between header and content of the response
        
            #Send the content of the requested file to the client
            for i in range(0, len(outputdata)):
                self.connectionSocket.send(outputdata[i].encode())
                self.connectionSocket.send("\r\n".encode())
            
            #Close the file
            f.close()
            
        except IOError:
            #Send response message for file not found
            self.connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
            self.connectionSocket.send("\r\n".encode())
            self.connectionSocket.send("404 Not Found\r\n".encode())
        
        finally:
            with self.lock:
                connection_counter -= 1
                print("Active connections: ", connection_counter)

serverSocket.listen(1) # Listen for incoming connections
serverSocket.settimeout(0.5) # Set a timeout for the socket to listen for interruptions

print('Ready to serve...')
try:
    while True:
        #Establish the connection
        try:
            connectionSocket, addr = serverSocket.accept()
            print("Connection established with: ", addr)

            # Create a new thread for each client connection
            new_thread = ClientThread(connectionSocket, addr, thread_lock)
            new_thread.start() # Start the thread
            threads.append(new_thread) # Append the thread to the list
            print("Thread started: ", new_thread)

        except timeout:
            pass
        except KeyboardInterrupt:
            print("\nServer shutting down...")
            break
        
except KeyboardInterrupt:
    print("\nServer shutting down...")
    pass

for t in threads:
    t.join() # Wait for all threads to finish

print("All threads have finished. Server is shutting down.")
serverSocket.close()
sys.exit() # Exit the program

