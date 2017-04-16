
import conectivity
import messages
import logging
import time



if __name__ == '__main__':

    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)
    
    connection = conectivity.Connection(logger, "192.168.56.1", 60173, 4096, 60, 0.1, 5)
    connection.start()
    msg = messages.MessageManualRegistration(3,
                                             set([messages.MessageManualRegistration.Floor(1, messages.MessageManualRegistration.Floor.DoorOpening.Types.FRONT),
                                                  messages.MessageManualRegistration.Floor(210, messages.MessageManualRegistration.Floor.DoorOpening.Types.BOTH)]), 
                                              messages.MessageManualRegistration.Attribution.Types.GENERAL, 
                                              0)
    
    connection.send(msg)
    
    time.sleep(120)
    
    msg = messages.MessageManualRegistration(3,
                                         set([messages.MessageManualRegistration.Floor(1, messages.MessageManualRegistration.Floor.DoorOpening.Types.FRONT),
                                              messages.MessageManualRegistration.Floor(210, messages.MessageManualRegistration.Floor.DoorOpening.Types.BOTH)]), 
                                          messages.MessageManualRegistration.Attribution.Types.GENERAL, 
                                          0)
    
    connection.send(msg)
    
    connection.stop()
    
