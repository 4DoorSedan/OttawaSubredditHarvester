#Main application for the comment puller application

import commentPuller
import getopt, sys
import sqlite3
import logging
import queue
import os.path as osPath

commentPullerLogger = logging.getLogger("Comment Puller")

isRunning = True

def main():
    #Get the command line argument that should be the path to the SQLite3 database
    cmd_arguments = sys.argv[1:]
    long_options = ["path="]
    short_options = ""
    try:        
        args, values = getopt.getopt(cmd_arguments, short_options, long_options)
    except getopt.error as err:
        commentPullerLogger.error("There was an issue with parsing the command line arguments: \n %",str(err))
        sys.exit(2)
    #Check if the path is valid and warn the user if a new db file is going to be created by the path and then open the file
    if osPath.isfile(values[0]):
        commentPullerLogger.info("Opening the database at %s"%values[0]) 
        dataBase = sqlite3.connect(values[0])
    else:
        if values[0][-3:] == ".db":
            print("The database at path {} does not appear to exsist. Would you like an empty database created with this name?".format(values[0]))
            if input("Y/n ").lower() == "y":
                dataBase = sqlite3.connect(values[0])
            else:
                commentPullerLogger.info("User did not want to create new database file. Terminating")
                sys.exit(0)
        else:
            print("The path {} does not appear to be a valid path to get to a database, please run the script again with the right path ".format(values[0])) 
            commentPullerLogger.error("User entered invalid path stopping excution of script")
            sys.exit(2)
    #Now we start the main loop of the program
    postsQueue = postQueue()
    #Start the thread of the comment looging here
    while(isRunning): #Main loop of the program
        #This part of the program is responsible for taking post out of the "POST_LINK" table and getting all of the the details
        pass







#This is a simple class to wrap some of the basic stuff for the post queue up into one spot
class postQueue:
    _MaxQueueSize = 0 #Set to zero for an unlimited size queue

    def __init__(self):
        self.Queue = queue.Queue(self._MaxQueueSize)

    def addPost(self, title: str, link: str):
        self.Queue.put((title, link)) #add as a tuple

    def getPost(self):
        return self.Queue.get() #Returns the tuple of title and link


if __name__ == "__main__":
    main()