#Main application for the comment puller application

from sqlite3.dbapi2 import Connection
from commentPuller import commentPuller
import getopt, sys
import sqlite3
import logging
import queue
import os.path as osPath
import time, threading
import RedditComment

commentPullerLogger = logging.getLogger("Comment Puller")

isRunning = True

def main():
    #Pulling in the global variables
    global _SQL_GetPostsToUpdate

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
    dataBase.execute(_SQL_CreateTable) #Create the table if it doesn't already exsists
    dataBase.commit()
    postsQueue = postQueue()   
    commentThread = commentGrabberThread(1, "Thread-1", 1, values[0], postsQueue)
    commentThread.start()
    while(isRunning): #Main loop of the program
        #This part of the program is responsible for taking post out of the "POST_LINK" table and getting all of the the details
        selectedPosts = dataBase.execute(_SQL_GetPostsToUpdate) #This is returning a cursor object!
        for (PostTitle, Link) in selectedPosts.fetchall():
            if (not postsQueue.isInQue(Link)):
                postsQueue.addPost(PostTitle, Link)
            time.sleep(1) #Space the requests out
        time.sleep(600)
        
  
     

#HERE BE SQL

#This SQL request should get all posts that have a last updated time of greater than 12 hours and are not archived
_SQL_GetPostsToUpdate = """
SELECT  post_title, link FROM POST_LINK 
WHERE NOT isArchived AND (Last_Updated IS NULL OR Last_Updated <= date('now', '-12 hours'))
ORDER BY Last_Updated DESC;
"""
#This SQL creates a tabel after checking if it already exsists
_SQL_CreateTable = """
CREATE TABLE IF NOT EXISTS Post_Data (
	"id" integer,
	"post_title" text not NULL,
	"author" text not NULL,
	"author_flair" text,
	"author_flair_text" text, 
	"ups" integer not NULL,
	"downs" integer not NULL,
	"score" integer not NULL,
	"total_awards_received" integer,
	"comment_id" text not NULL,
	"parent_id" text not NULL,
	"body_text" text not NULL,
    "isReply" BOOLEAN not NULL,
	"created_utc" integer not NULL,
	"time_last_pulled" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY ("id")
);
"""
#Adds a full row of information to the database
_SQL_AddDataRow = """
INSERT INTO Post_Data(post_title, author, author_flair, author_flair_text, ups, downs, score, total_awards_received, comment_id, parent_id, body_text, isReply, created_utc)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);
"""
#Returns any row with the subed in comment_id (used to check if already in DB)
_SQL_CheckExsistenceQuery = """
SELECT DISTINCT comment_id FROM POST_DATA
WHERE comment_id = ?;
"""

#Upates the post_Data table with updated information
_SQL_UpdatePostData = """
UPDATE Post_Data
SET ups = ?,
	downs = ?,
	score = ?,
	total_awards_received = ?,
	body_text = ?,
	time_last_pulled = CURRENT_TIMESTAMP
WHERE 
	comment_id = ?;	
"""

#Updates the post_link table with the new updated time
_SQL_UpdatePostLinkTable = """
UPDATE POST_LINK
SET Last_Updated = CURRENT_TIMESTAMP
WHERE post_title = ? AND link = ?;
"""

#This is a simple class to wrap some of the basic stuff for the post queue up into one spot
class postQueue:
    _MaxQueueSize = 0 #Set to zero for an unlimited size queue

    def __init__(self):
        self.Queue = queue.Queue(self._MaxQueueSize)
        self._listofPostLinks = [] #This is a list of all post titles currently in the queue

    def addPost(self, title: str, link: str):
        self.Queue.put((title, link)) #add as a tuple
        self._listofPostLinks.append(link)

    def getPost(self):
        item = self.Queue.get() #Returns the tuple of title and link
        (postTitle, Link) = item
        self._listofPostLinks.remove(Link)
        return item

    def isInQue(self, postLink :str):
        if (self._listofPostLinks.count(postLink) == 0):
            return False
        else:
            return True

    def isEmpty (self):
        return self.Queue.empty()
    
#This is the comment gathering thread of the program
#This was taken from the website -> https://www.tutorialspoint.com/python/python_multithreading.htm
#
#This contains all of the functions required for getting all of the comments and adding them to the database
class commentGrabberThread (threading.Thread):
    def __init__(self, threadID, name, counter, dataBasePath: str, queue: postQueue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.databasePath = dataBasePath
        self.postsQueue = queue

    def run(self):
        #Main running loop of the thread
        while(isRunning):
            databaseConnection = sqlite3.connect(self.databasePath)
            if (not self.postsQueue.isEmpty()):
                (postTitle, postLink) = self.postsQueue.getPost()
                listOfComments = commentPuller(postLink, postTitle)
                for comment in listOfComments.comments(): #Iterate through all of the comments 
                    commentData = comment._commentData
                    for (key, value) in commentData.items(): #This for loop will remove all the NONE types in the
                        if (value == None):                 #TODO: THIS needs to be fixed
                            commentData[key] = ""
                    checkCursor = databaseConnection.execute(_SQL_CheckExsistenceQuery, (commentData["id"],))                   
                    if (checkCursor.fetchone() == None): #Will return none if the excute didn't find anything
                        #Add in the new unique row 
                        databaseConnection.execute(_SQL_AddDataRow, (postTitle, commentData["author"], commentData["author_flair_css_class"], 
                        commentData["author_flair_text"], commentData["ups"], commentData["downs"], commentData["score"], commentData["total_awards_received"], commentData["id"], commentData["parent_id"], commentData["body"], commentData["isReply"], commentData["created_utc"]))
                        databaseConnection.commit()
                    else:
                        databaseConnection.execute(_SQL_UpdatePostData, (commentData["ups"], commentData["downs"], commentData["score"], commentData["total_awards_received"], commentData["body"], commentData["id"]))
                        databaseConnection.commit()
                    #Update the Post Link table with the new update time
                databaseConnection.execute(_SQL_UpdatePostLinkTable, (postTitle, postLink))
                databaseConnection.commit()
                commentPullerLogger.info(f"Logged comments from: {postTitle}  {postLink}")
                print(f"Updated info for {postTitle}")
                time.sleep(1) #Wait inbetween requests to avoid hitting the max time
                    
            
            else:
                time.sleep(30) #If there isn't any comments in the que then the thread should probably wait for a while 

              

if __name__ == "__main__":
    main()


