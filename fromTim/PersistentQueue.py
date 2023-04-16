import fileQueue
from fileQueue import OK
from fileQueue import NO_MORE_MESSAGES
import time
#olfrom time import localtime, strftime
import os


class PERSISTENTQUEUE():

    testingFilename = "somename.txt"
    
    def __init__(self):
        print("init persistentQueue")
    
    def fileExists(self, filename ):
        try:
            os.stat( filename)
            return True
        except OSError:
            return False
            
    def Test1(self):
        '''
        Test 1
        - removal with no file
        '''

        print("Test 1")
        file = fileQueue.FILEQUEUE(self.testingFilename)

        errorCode, returnMessage = file.removeFromQueue( message = "return message" )
        print("errorCode: ", str(errorCode) + " :returned message: " + returnMessage)

        if self.fileExists(self.testingFilename):
            print("file shouldn't exist.  Should all be taken care of in the fileQueue class ")
            exit
    
        return
    
    def Test2(self):
    
        '''
        Test 2
        - add one message, 
        - remove message
        - remove remove file
        '''
        
        print("Test 2")
        file = fileQueue.FILEQUEUE(self.testingFilename)

        stringtime= str(time.localtime())
        print("localtime(): ", time.localtime())
        print("Write message: " + stringtime )
        file.addToQueue( stringtime + " data in file")

        errorCode, returnMessage = file.removeFromQueue( message = "return message" )
        print("errorCode: ", str(errorCode) + " :returned message: " + returnMessage)

        if self.fileExists(self.testingFilename):
            print("file shouldn't exist.  Should all be taken care of in the fileQueue class ")
            exit
         
        return
       
    def Test3(self):
        '''
        Test 3
        - add multiple messages, 
        - remove all messages
        - remove file
        '''
        
        print("Test 3")
        file = fileQueue.FILEQUEUE(self.testingFilename)

        for i in range(1):
            stringtime = str(i) + ": " + str(time.localtime())
            print("Write message: " + stringtime )
            file.addToQueue( stringtime + " data in file")
            time.sleep(1)

        for i in range(1):
            errorCode, returnMessage = file.removeFromQueue( message = "return message" )
            print("errorCode: ", str(errorCode) + " :returned message: " + returnMessage)
            if(errorCode == NO_MORE_MESSAGES):
                print("No more messages")
                break

        if self.fileExists(self.testingFilename):
            print("file shouldn't exist.  Should all be taken care of in the fileQueue class ")
            exit
        
        return
    
    
    def Test4(self):
    
        '''
        Test 4
        - add multipe messages, 
        - remove some messages, 
        - add some messages, 
        - remove remaining messages
        - remove file
        '''
        
        print("Test 4")
        file = fileQueue.FILEQUEUE(self.testingFilename)

        for i in range(10):
            stringtime = str(i) + ": " + str(time.localtime())
            print("Write message: " + stringtime )
            file.addToQueue( stringtime + " data in file")
            time.sleep(1)

        for i in range(5):
            errorCode, returnMessage = file.removeFromQueue( message = "return message" )
            print("errorCode: ", str(errorCode) + " :returned message: " + returnMessage)


        for i in range(7):
            stringtime= str(i) + ": " + str(time.localtime())
            print("Write message: " + stringtime )
            file.addToQueue( stringtime + " data in file")
            time.sleep(1)

        errorCode, returnMessage = file.removeFromQueue( message = "return message" )
        print("errorCode: ", str(errorCode) + " :returned message: " + returnMessage)
        while errorCode == OK:
            errorCode, returnMessage = file.removeFromQueue( message = "return message" )
            print("errorCode: ", str(errorCode) + " :returned message: " + returnMessage)

        if self.fileExists(self.testingFilename):
            print("file shouldn't exist.  Should all be taken care of in the fileQueue class ")
            exit

        
        return
    
    
    def runTests(self):
    
        self.testingFilename = "dataQueue.txt"


        # make sure to start in a known configuration 
        if self.fileExists(self.testingFilename):
            os.remove( self.testingFilename)

        print("starting tests")
        self.Test1()
        self.Test2()
        self.Test3()
        self.Test4()
        
        print("finished")
        return
