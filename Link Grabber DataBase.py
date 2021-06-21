import requests
import sqlite3
import string
from time import sleep

SUBREDDIT = "ottawa"
PULL_NUMBER = 10
LISTING = "new"
TIMEFRAME = "day"
VERBOSE = True
SLEEP_TIME = 30

def main():
    RUN = True
    loggedData = {}
    newData = {}
    #Get the connection to the database. Should repeat the promt until a valid one is returned from create_connection()
    dbConnection = None
    while not dbConnection:
        dbPath = input("Path to DB?")
        if not ".db" in dbPath: #Makes sure that .db goes on the end. Could be fooled by an idiot putting .db somewhere in the filename it shouldn't be
            dbPath = dbPath + ".db" 
        dbConnection = create_connection(dbPath)
    cursor  = dbConnection.cursor()
    cursor.execute(_SQL_CREATE_TABLE_COMMAND) #Creates the link table 

    #Start the main loop of the program 
    while RUN:
        RedditData = {}
        pullData(RedditData)
        for key in RedditData.keys():
            if not RedditData['{}'.format(key)]["data"]["title"] in loggedData:
                permaLink = "https://www.reddit.com/{}".format(RedditData['{}'.format(key)]['data']['permalink'])
                loggedData.update({key : permaLink}) #This is where all records will live
                newData.update({key: permaLink}) #This will just be new data that needs to be added to the DB, this will cut down on the number of databases calls
        #AddData to table
        for key in newData.keys():
            translator = str.maketrans('', '', string.punctuation)
            saniText = str(key).translate(translator)
            cursor.execute(_SQL_SELECT_SANATIZED, [saniText])
            if cursor.fetchone() == None:
                cursor.execute(_SQL_ADD_ROW_POST_LINK, (saniText, str(key), newData[str(key)]))
                dbConnection.commit()
                print("Added post with title {} to db".format(str(key))) if VERBOSE else print("")
            else: 
                print("Post with title of {} was already in the database somehow".format(str(key)))
        newData.clear()
        sleep(SLEEP_TIME)



#Funcion for pulling down the json data from reddit
def pullData(DataDict: dict):
    URL = f"https://www.reddit.com/r/{SUBREDDIT}/{LISTING}/.json?limit={PULL_NUMBER}&t={TIMEFRAME}"
    response = {}
    try: 
        response = requests.get(URL, headers={"User-agent" : "yourbot"}, timeout=120)
    except:
        print("Error with catching data from reddit. Consult log")
    #Push all the comment data into the passed in dictionary 
    rawdata=response.json()
    DataDict.clear()
    for comment in rawdata['data']['children']:
        newData = {comment['data']['title'] : comment}
        DataDict.update(newData)

#Connects to the database
def create_connection(dbPath):
    conn = None
    #Make sure that this will be a .db file
    try:
        conn = sqlite3.connect(dbPath)
        print("Database was sucessfully connected")
        return conn
    except sqlite3.Error as e:
        print("Was unable to connect to the database")


_SQL_SELECT_SANATIZED = "SELECT post_title_sanatized FROM POST_LINK WHERE post_title_sanatized = ?;"

_SQL_ADD_ROW_POST_LINK = "INSERT INTO POST_LINK (post_title_sanatized, post_title, link) VALUES (?,?,?);"

_SQL_CREATE_TABLE_COMMAND = """CREATE TABLE IF NOT EXISTS POST_LINK (
	id integer PRIMARY KEY,
    post_title_sanatized text NOT NULL,
	post_title text NOT NULL,
	link text NOT NULL
);"""

if __name__ == "__main__":
    main()