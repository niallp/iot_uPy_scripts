#from os import path
#import os.path
import os

#error codes
NO_MORE_MESSAGES = 2
OK = 1


class FILEQUEUE():
    #initiailzie class variables
    queueFilename = "dummyname"
    #initialize class
    def __init__(self, filename="queue.txt"):
        #self.queueFilename = filename
        self.queueFilename = filename
 
    def fileExists(self):
        try:
            os.stat(self.queueFilename)
            return True
        except OSError:
            return False
  
    def addToQueue(self, message = "stale message"):
        #if the file exists, then just add the message to the end of the file
        if self.fileExists():
            fp=open(self.queueFilename, 'a')
            # write message
            fp.write( message +"\n")
            fp.close()
        else:
            #if file does not exist, write file with read pointer and at line 2 add message, close 
            #currently, the read pointer is 11 digits.  need to calculate if this is enough.  
            #The specific size of the readpointer is used to make sure we don't overwrite any subsequent 
            #bytes.  It is overwriten to track the location of already transmitted data
            #while all the other timestamped data is appended.
            fp = open(self.queueFilename, 'a')
            #write read pointer
            fp.write(f"{11:0>10d}" + '\n')
            fp.write(message + '\n')
            fp.close()
    
    def removeFromQueue ( self ):
        #if file doesn't exist, return NO_MORE_MESSAGES

        message = "no data"
        if(self.fileExists()):
            fp=open(self.queueFilename, 'r+')
            fp.seek(0)
            readPointer = int(fp.readline())
            fp.seek(readPointer)
            message = fp.readline()
            if message:
                #new read pointer after readline
                readPointer = fp.tell()
                #write new read pointer
                fp.seek(0)
                formattedData = f"{readPointer:0>10d}"
                fp.write(formattedData)
                errorCode = OK
                #check for end of file
                fp.seek(0,2)
                checkForEndOfFilePointer = fp.tell()
                fp.close()

                if checkForEndOfFilePointer == readPointer:
                    os.remove(self.queueFilename)
                    errorCode = NO_MORE_MESSAGES
                
            else:
                fp.close()
                os.remove(self.queueFilename)
                errorCode = NO_MORE_MESSAGES
        else:
            errorCode = NO_MORE_MESSAGES

        return errorCode, message[:-1]
        
  
