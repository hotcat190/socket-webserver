from queue import Queue
from argparse import ArgumentParser
from socket import *
from threading import Thread

# Initialize instance of an argument parser
parser = ArgumentParser(description='Multi-threaded TCP Client')

# Add optional arguments, with given default values if user gives no args
parser.add_argument('-r', '--requests', default=10, type=int, help='Total number of requests to send to server')
parser.add_argument('-w', '--workerThreads', default=5, type=int, help='Max number of worker threads to be created')
parser.add_argument('-i', '--ip', default='localhost', help='IP address to connect over')
parser.add_argument('-p', '--port', default=12000, type=int, help='Port over which to connect')
parser.add_argument('-f', '--file', default='HelloWorld.html', help='The full path to the requested object stored at the server')

# Get the arguments
args = parser.parse_args()

class Client:
    def __init__(self, id, address, port, message):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.id = id
        self.address = address
        self.port = port
        self.message = str(message)

    def run(self):
        try:
            self.socket.settimeout(5) # Timeout if the no connection can be made in 5 seconds 
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # Allow socket address reuse
            self.socket.connect((self.address, self.port)) # Connect to the ip over the given port
            self.socket.send(self.message.encode()) # Send the defined request message
            
            while True:
                try:
                    data = self.socket.recv(1024) # Wait to receive data back from server
                    print(self.id, ":  received: ", data.decode()) # Notify that data has been received
                    if not data:
                        break
                except timeout:
                    break # If no data is received, break out of the loop

            self.socket.close() # Close the socket connection
            print(self.id, ":  closed connection to ", self.address, " over port", self.port)
        except error as e:
            print("\nERROR: Could not connect to ", self.address, " over port", self.port, "\n")
            raise e

# Create a queue to hold the tasks for the worker threads
q = Queue(maxsize=0)

# Function which generates a Client instance, getting the work item to be processed from the queue
def worker():
    message = "GET /" + args.file + " HTTP/1.1\r\nHost: " + args.ip + "\r\n\r\n"

    while True:
        # Get the task from the work queue
        item = q.get()

        new_client = Client(item, args.ip, args.port, message)
        new_client.run()
        # Mark this task item done, thus removing it from the work queue
        q.task_done()

# Populate the work queue with a list of numbers as long as the total number of requests wished to be sent.
# These queue items can be thought of as decrementing counters for the client thread workers.
for item in range(args.requests):
    q.put(item)

# Create a number of threads, given by the workerThreads variable, to initiate clients and begin sending requests.
for i in range(args.workerThreads):
    t = Thread(target=worker)
    t.daemon = True
    t.start()

# Do not exit the main thread until the sub-threads complete their work queue
q.join()
