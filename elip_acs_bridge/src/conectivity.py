import collections
import errno
import messages
import socket
import threading
import time

#=======================================================================================================================
class Connection(object):
    
    def __init__(self, logger, hostname, port, receiveBuffSize, healthCheckPeriod, idleTime, connectionRetryTimeout):
        """ C'tor
        @param logger: Logger 
        @param hostname: Hostname of the E-LIP controller
        @param port: TCP Port of the E-LIP controller
        @param receiveBuffSize: Size in bytes of receiving buffer 
        @param healthCheckPeriod: Period in seconds in which a health check message will be sent
        @param idleTime: Time to idle between cycles
        @param connectionRetryTimeout: Timeout in seconds between connection retries
        """

        self.__connector = _Connector(logger, hostname, port, receiveBuffSize, )
        self.__logger = logger
        self.__shouldRun = False
        self.__idleTime = idleTime
        self.__healthCheckCycle = healthCheckPeriod / idleTime
        self.__queue = collections.deque()
        self.__thread = threading.Thread(target = self.__target)
        self.__connectionRetryTimeout = connectionRetryTimeout

    def send(self, message):
        """ Enqueue a message to be sent to E-LIP controller
        @param: Message to send
        """
        
        self.__queue.appendleft(message)
        
    def start(self):
        """ Start the connection thread
        """
        
        self.__shouldRun = True
        self.__thread.start()
        
    def stop(self):
        """ Stop the connection thread
        """
        
        self.__shouldRun = False
        self.__thread.join()
    
    def __target(self):
        """ Thread target
        """
        
        cycleNum = 0
        
        self.__logger.info("Starting connection to E-LIP")
        
        while self.__shouldRun:
            
            try:
            
                if self.__connector.isConnected:
    
                    # Sending health check
                    if cycleNum % self.__healthCheckCycle == 0:
                        messageToSend = messages.MessageHealthCheck()
                        self.__logger.debug("Sending message: %s" % (messageToSend, ))
                        self.__connector.send(messageToSend)

                    # Receiving message and logging                        
                    receivedMessage = self.__connector.receive()
                    
                    if receivedMessage is not None:
                        self.__logger.info("Received message: %s" % (receivedMessage, ))

                    # Sending message if has one                        
                    if self.__queue:
                        messageToSend = self.__queue.pop()
                        self.__logger.info("Sending message: %s" % (messageToSend, ))
                        self.__connector.send(messageToSend)
                    
                else: 
                    self.__connector.connect()
                
            except _ConnectionError:
                time.sleep(self.__connectionRetryTimeout)
            
            except:
                self.__logger.exception("Unexpected exception")
                
            cycleNum += 1
            time.sleep(self.__idleTime)
                
        self.__connector.close()                
        self.__logger.info("Stopping connection to E-LIP") 

#=======================================================================================================================
class _Connector(object):
   
#-----------------------------------------------------------------------------------------------------------------------   
    def __init__(self, logger, hostname, port, receiveBuffSize):
        """ C'tor
        @param hostname: Hostname of the E-LIP controller
        @param port: TCP Port of the E-LIP controller
        @param receiveBuffSize: Size in bytes of receiving buffer 
        """
        
        self.__hostname = hostname
        self.__port = port
        self.__receiveBuffSize = receiveBuffSize
        self.__logger = logger
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.__isConnected = False
        self.__messageFactory = messages.Factory(logger)
        
#-----------------------------------------------------------------------------------------------------------------------   
    @property
    def isConnected(self): return self.__isConnected        
        
#-----------------------------------------------------------------------------------------------------------------------       
    def connect(self):
        """ Connect to the E-LIP controller
        """
        
        while not self.__isConnected:
            
            try:
                self.__logger.info("Connecting to %s:%s" % (self.__hostname, self.__port))
                self.__socket.connect((self.__hostname, self.__port))
                self.__socket.setblocking(0)
                self.__isConnected = True
            
            except socket.error as e:
                self.__logger.error("Failed connecting to %s:%s - %s" % (self.__hostname, self.__port, e))
                self.__reset()
                
                raise _ConnectionError() 
                
#-----------------------------------------------------------------------------------------------------------------------       
    def send(self, message):                
        """ Send a message to E-LIP controller
        @param message: Message to send
        """
        
        try:
            self.__socket.send(message.getAsBytes())
            
        except socket.error as e:
            self.__logger.error("Failed sending message: %s - %s" % (message, e))
            self.__reset()
            
            raise _ConnectionError(e) 
        
#-----------------------------------------------------------------------------------------------------------------------       
    def receive(self):                
        """ Receive a message to E-LIP controller
        @return message from E-LIP controller or None if no data
        """
        
        try:
            payload = bytearray(self.__socket.recv(messages.MessageInterface._SIZE_HEADER))
            payload.extend(self.__socket.recv(payload[messages.MessageInterface.OFFSET_HEADER_DATA_LENGTH_FIELD]))
            return self.__messageFactory.create(payload)
        
        except socket.error as e:
            
            if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                self.__logger.debug("No data received on socket")
                return None

            else:
                self.__logger.error("Failed receiving data from socket - %s" % (e,))
                self.__reset()
                
                raise _ConnectionError()     
                
        except IndexError:
            
                # An index error occurs when E-LIP closes its socket thus we receive an EOF and an empty bytes object
                # which leads to an index error
                self.__logger.error("Connection was closed by remote peer")
                self.__reset()
              
                raise _ConnectionError()      
        
#-----------------------------------------------------------------------------------------------------------------------       
    def close(self):
        """ Close connection to the E-LIP controller
        """
        
        if self.__isConnected:
            self.__logger.info("Disconnecting from %s:%s" % (self.__hostname, self.__port))
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__isConnected = False

#-----------------------------------------------------------------------------------------------------------------------                
    def __reset(self):
        """ Reset the connector to non connected state
        """
        
        self.__socket.close()
        self.__isConnected = False
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            
#=======================================================================================================================
class _ConnectionError(Exception):
    pass
        