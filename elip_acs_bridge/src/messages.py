import collections

#=======================================================================================================================
class MessageInterface(object):
    
    OFFSET_HEADER_DATA_LENGTH_FIELD = 0x0
    
    _COMMAND_MANUAL_REGISTRATION   = 0x20
    _COMMAND_HEALTH_CHECK          = 0x11
    _COMMAND_REGISTRATION_RESPONSE = 0x90
    
    _SIZE_HEADER                   = 0x04
    _SIZE_HEADER_DATA_LENGTH_FIELD = 0x1
    _SIZE_COMMAND_FIELD            = 0x01
    
    _OFFSET_HEADER_VERSION_FIELD = _SIZE_HEADER_DATA_LENGTH_FIELD
    _OFFSET_COMMAND_FIELD        = _SIZE_HEADER
    
    _HEADER_VERSION                      = 0x41 # 'A'
    _HEADER_LENGTH_MANUAL_REGISTRATION   = 0x4c
    _HEADER_LENGTH_HEALTH_CHECK          = 0x04
    _HEADER_LENGTH_REGISTRATION_RESPONSE = 0x06

#-----------------------------------------------------------------------------------------------------------------------         
    def getAsBytes(self):
        """ Get a bytes object representation of the message which could be sent over a connector
        @attention: To be implemented by derived
        @return a bytes object representation of the message which could be sent over a connector
        """ 
        
        pass   

#=======================================================================================================================
class MessageRegistrationResponse(MessageInterface):

    __SIZE_SEQUENCE_NUMBER_FIELD      = 0x01
    __SIZE_ASSIGNED_CAR_NUMBER_FIELD  = 0x03
    __SIZE_ASSIGNED_BANK_NUMBER_FIELD = 0x03
    
    __OFFSET_SEQUENCE_NUMBER_FIELD      = MessageInterface._SIZE_HEADER + MessageInterface._SIZE_COMMAND_FIELD
    __OFFSET_ASSIGNED_CAR_NUMBER_FIELD  = __OFFSET_SEQUENCE_NUMBER_FIELD + __SIZE_SEQUENCE_NUMBER_FIELD
    __OFFSET_ASSIGNED_BANK_NUMBER_FIELD = __OFFSET_ASSIGNED_CAR_NUMBER_FIELD + __SIZE_ASSIGNED_BANK_NUMBER_FIELD

#-----------------------------------------------------------------------------------------------------------------------   
    def __init__(self, bytes_):
        """ C'tor
        @param bytes_: A bytes object representing the response
        """

        self.__bytes = bytes
        self.__sequenceNumber = self.__bytes[self.__OFFSET_SEQUENCE_NUMBER_FIELD]
        self.__assignedCarNumber = int(self.__bytes[self.__OFFSET_ASSIGNED_CAR_NUMBER_FIELD : 
                                                    self.__OFFSET_ASSIGNED_BANK_NUMBER_FIELD].decode("ascii"))
        self.__assignedBankNumber = int(self.__bytes[self.__OFFSET_ASSIGNED_BANK_NUMBER_FIELD].decode("ascii"))
        
#-----------------------------------------------------------------------------------------------------------------------  
    def __repr__(self): 
        return "MessageRegistrationResponse(sequenceNumber=%s, assignedCarNumber=%s, assignedBankNumber=%s)" % (
                                            self.__sequenceNumber, self.__assignedCarNumber, self.__assignedBankNumber)

#-----------------------------------------------------------------------------------------------------------------------
    @property    
    def sequenceNumber(self): return self.__sequenceNumber
    
#-----------------------------------------------------------------------------------------------------------------------    
    @property
    def assignedCarNumber(self): return self.__assignedCarNumber

#-----------------------------------------------------------------------------------------------------------------------    
    @property
    def assignedBankNumber(self): return self.__assignedBankNumber
    
#-----------------------------------------------------------------------------------------------------------------------         
    def getAsBytes(self): 
        """
        @see: Interface documentation
        """
        
        return self.__bytes         

#=======================================================================================================================    
class MessageManualRegistration(MessageInterface):
    
    __CARD_NUMBER_MIN     = 0
    __CARD_NUMBER_MAX     = 255
   
    __SEQUENCE_NUMBER_MAX = 0
    __SEQUENCE_NUMBER_MAX = 255
    
    __FLOOR_NUMBER_MIN    = 1
    __FLOOR_NUMBER_MAX    = 255
    
    __SIZE_CARD_NUMBER_FIELD = 0x04
    
    __OFFSET_ACCESIBLE_FLOORS = MessageInterface._SIZE_HEADER + MessageInterface._SIZE_COMMAND_FIELD + \
                                __SIZE_CARD_NUMBER_FIELD
    
    
    class Attribution(object):
        class Types(object):
            GENERAL       = 0x30 # '0'
            HANDICAPPED   = 0x31 # '1'
            VIP           = 0x32 # '2'
    
    class Floor(collections.namedtuple("Floor", "number doorOpening")):
        """ C'tor
        @param number: The floor number
        @param doorOpening: How should the doors be opened
        """
        
        class DoorOpening(object):
            class Types(object):
                NONE  = 0 # 00
                FRONT = 1 # 01
                REAR  = 2 # 10
                BOTH  = 3 # 11

        def __repr__(self): return "Floor(number=%s, doorOpening=%s)" % (self.number,
                                                                    ["NONE", "FRONT", "REAR", "BOTH"][self.doorOpening])
        
        def __hash__(self): return self.number
        
#-----------------------------------------------------------------------------------------------------------------------     
    def __init__(self, cardReaderNumber, accesibleFloors, attribution, sequenceNumber):
        """ C'tor
        @param cardReaderNumber: Swiped card number as integer
        @param accessibleFloors: A set() of accessible floors
        @param attribution: Specific attribution
        @param sequenceNumber: Message sequence number
        """ 
        
        if cardReaderNumber < self.__CARD_NUMBER_MIN or cardReaderNumber > self.__CARD_NUMBER_MAX:
            raise StructureError("Card number should be in range of 0 - %s" % (self.__CARD_NUMBER_MIN, 
                                                                               self.__CARD_NUMBER_MAX))
        
        if sequenceNumber < 0 or sequenceNumber > self.__SEQUENCE_NUMBER_MAX:
            raise StructureError("Sequence number should be in range of 0 - %s" % (self.__SEQUENCE_NUMBER_MIN, 
                                                                                   self.__SEQUENCE_NUMBER_MAX))
             
        self.__cardReaderNumber = cardReaderNumber
        self.__accesibleFloors = sorted(accesibleFloors)
        self.__attribution = attribution
        self.__sequenceNumber = sequenceNumber
        
        strCardReaderNumber = "%04d" % cardReaderNumber
        
        self.__bytes = bytearray([self._HEADER_LENGTH_MANUAL_REGISTRATION,           # Length byte       
                                  self._HEADER_VERSION,                              # Version byte
                                  0x00, 0x00,                                        # 2 Reserved bytes
                                  self._COMMAND_MANUAL_REGISTRATION,                 # Command byte                               
                                  strCardReaderNumber[0],                            # Card reader number as 4 chars
                                  strCardReaderNumber[1],
                                  strCardReaderNumber[2], 
                                  strCardReaderNumber[3],  
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,    # 64 Bytes of non allowed floors
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                  self.__attribution,                                 # Attribution char
                                  sequenceNumber,                                     # Sequence number byte
                                  0x00, 0x00, 0x00, 0x00, 0x00])                      # 5 Reserved bytes
        
        # Build the floors byte array
        for floor in self.__accesibleFloors:
            
            if floor.number < self.__FLOOR_NUMBER_MIN or floor.number > self.__FLOOR_NUMBER_MAX:
                raise StructureError("Floor number should be in range of %s - %s" % (self.MIN_NUMBER, 
                                                                                     self.MAX_NUMBER))
            
            # Floor number -1 since minimal floor number is 1 but 0 in our array
            # *2 to get the lowest bit location of the floor and /8 for the byte location within the array
            # Example: Floor 242 -> ((242 - 1) * 2) / 8 = 60 Which is exactly the 61th byte
            byteIndex = int(((floor.number - 1) * 2) / 8) 
            
            # Now add the correct message offset
            byteIndex +=  self.__OFFSET_ACCESIBLE_FLOORS
            
            # Floor number -1 since minimal floor number is 1 but 0 in our array
            # We have 4 floors in one bytes, so the location of a floor is determined by %4, but each floor takes 2 bits
            # So we need to *2
            # Example Floor 242 -> ((242 - 1) % 4) * 2 = 2 Which is exactly the 3rd bit shift left offset
            doorOpeningOffset = (((floor.number - 1) % 4) * 2)
            
            # Now we just place it 
            byteValue = self.__bytes[byteIndex]
            self.__bytes[byteIndex] = byteValue | (floor.doorOpening << doorOpeningOffset)
            
        # Now immutable it
        self.__bytes = bytes(self.__bytes)

#-----------------------------------------------------------------------------------------------------------------------  
    def __repr__(self): 
        return "MessageManualRegistration(cardReaderNumber=%s, accesibleFloors=%s, attribution=%s, sequenceNumber=%s)"\
                 % (self.__cardReaderNumber, self.__accesibleFloors, 
                   (["GENERAL", "HANDICAPPED", "VIP"][self.__attribution - 0x30]), self.__sequenceNumber)

#----------------------------------------------------------------------------------------------------------------------- 
    @property
    def cardReaderNumber(self): return self.__cardReaderNumber

#-----------------------------------------------------------------------------------------------------------------------         
    @property
    def accesibleFloors(self): self.__accesibleFloors

#-----------------------------------------------------------------------------------------------------------------------         
    @property
    def attribution(self): self.__attribution

#-----------------------------------------------------------------------------------------------------------------------         
    @property
    def sequenceNumber(self): self.__sequenceNumber      
        
#-----------------------------------------------------------------------------------------------------------------------         
    def getAsBytes(self): 
        """
        @see: Interface documentation
        """
        
        return self.__bytes     
    
#=======================================================================================================================    
class MessageHealthCheck(MessageInterface):
    
#-----------------------------------------------------------------------------------------------------------------------   
    def __init__(self):
        self.__bytes = bytearray([self._HEADER_LENGTH_HEALTH_CHECK,           # Length byte       
                                self._HEADER_VERSION,                         # Version byte
                                0x00, 0x00,                                   # 2 Reserved bytes
                                self._COMMAND_HEALTH_CHECK,                   # Command byte                               
                                0x00, 0x00, 0x00])                            # 3 reserved bytes            

#-----------------------------------------------------------------------------------------------------------------------  
    def __repr__(self): 
        return "MessageHealthCheck()"
    
#-----------------------------------------------------------------------------------------------------------------------         
    def getAsBytes(self): 
        """
        @see: Interface documentation
        """
        
        return self.__bytes              
        
        
#=======================================================================================================================
class StructureError(Exception):
    pass

#=======================================================================================================================
class Factory(object):
    
#-----------------------------------------------------------------------------------------------------------------------          
    def __init__(self, logger):
        """ C'tor
        @param logger: Logger
        """
        
        self.__logger = logger

#-----------------------------------------------------------------------------------------------------------------------              
    def create(self, bytes_):
        """ Create a message from bytes object
        @param bytes_: Bytes object to create message from
        @return Message or None if received unidentified data 
        """ 
        
        if bytes_[MessageInterface._OFFSET_HEADER_VERSION_FIELD] != MessageInterface._HEADER_VERSION:
            self.__logger.warning("Received unknown protocol version data: %x" % (
                                                            bytes_[MessageInterface._OFFSET_HEADER_VERSION_FIELD], ))
            
            return None
        
        if bytes_[MessageInterface._OFFSET_COMMAND_FIELD] == MessageInterface._COMMAND_REGISTRATION_RESPONSE:
            return MessageRegistrationResponse(bytes_)
        
        else:
            self.__logger.warning("Received unexpected command field: %x" % (
                                                            bytes_[MessageInterface._OFFSET_COMMAND_FIELD], ))        
        
            return None
        