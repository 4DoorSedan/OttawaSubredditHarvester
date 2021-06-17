from os import write
import sys
import requests
import json
from time import sleep, strftime
from datetime import date
from threading import Thread, Lock, Timer

#Global Constants
VERBOSE = False
THREAD_LOCK = Lock()
SUBREDDIT = "ottawa"
PULL_NUMBER = 10
LISTING = "new"
TIMEFRAME = "day"
INTERVAL = 25




def main():
    #Script Variables
    global THREAD_LOCK
    currentDate = date.today()
    logFileName = currentDate.strftime("%Y-%m-%d") + ".json"
    rawData = {}
    loggedData = {}

    #Check if data needs to be loaded in
    try:
         oldFile = open(logFileName)
    except FileNotFoundError:
        print("No file matching current date found on resume")
    except IOError:
        print("Program was unable to read the file, continouing without data")
    else:
        sleep(10)
        #CODE FOR READING THE FILE HERE

    #Start data gatehring timer
    dataTimer = RepeatedTimer(INTERVAL, pullData, rawData)
    dataTimer.start()
    print("Data harvesting timer has been started")

    #Main program loop
    RunState = True
    while RunState:
        THREAD_LOCK.acquire()
        localDataCopy = rawData.copy()
        THREAD_LOCK.release()
        for key in localDataCopy.keys():
            if not localDataCopy['{}'.format(key)]["data"]["title"] in loggedData:
                permaLink = "https://www.reddit.com/{}".format(localDataCopy['{}'.format(key)]['data']['permalink'])
                loggedData.update({key : permaLink})
                if VERBOSE == True:
                    print(f"Added Comment with tittle {key}")
                
        #Log data to file every 24 hours
        if not currentDate == date.today():
            writeLoggedData(loggedData, currentDate)
            currentDate = date.today()
        #This section of code is for handling any kind of user input
        userInput = ""#input()
        if userInput == "Exit":
            writeLoggedData(loggedData, currentDate)
            RunState = False
        elif userInput == "Hard Exit":
            sys.exit()
        elif userInput == "Log Data":
            writeLoggedData(loggedData, currentDate+"-FORCEDLOG")
        elif userInput == "Pause":
            dataTimer.stop()
        elif userInput == "Resume":
            dataTimer.start()
        elif userInput == "Count":
            print("The current number of logged comments is {}".format(len(loggedData)))
        elif userInput == "Help":
            print("\n The following are viable commands:")
            print("\n Exit - Logs all currently held data and then exits the program")
            print("\n Hard Exit - Exits the program without logging any of the current data")
            print("\n Log Data - Saves the current data to a file")
            print("\n Pause - Pauses the timer controling the gathering of data")
            print("\n Resume - Resumes the timer controlling data harvesting after pausing")
            print("\n Count - Returns the current number of logged comments")

        sleep(33.33)
            


#Function for writing the JSON File
def writeLoggedData(Data: dict, fileDate: str):
    fileName = fileDate.strftime("%Y-%m-%d") + ".json"
    with open(fileName, mode="w") as json_file:
        json.dump(Data, json_file)
        print(f'{len(Data)} comments have been logged to the file {fileName}.json')
        json_file.close

#Funcion for pulling down the json data from reddit
def pullData(DataDict: dict):
    global THREAD_LOCK
    URL = f"https://www.reddit.com/r/{SUBREDDIT}/{LISTING}/.json?limit={PULL_NUMBER}&t={TIMEFRAME}"
    response = {}
    try: 
        response = requests.get(URL, headers={"User-agent" : "yourbot"}, timeout=120)
    except:
        print("Error with catching data from reddit. Consult log")
    #Push all the comment data into the passed in dictionary 
    rawdata=response.json()
    THREAD_LOCK.acquire()
    DataDict.clear()
    for comment in rawdata['data']['children']:
        newData = {comment['data']['title'] : comment}
        DataDict.update(newData)
    THREAD_LOCK.release()
    
#Class taken from stack overflow to handle the timing 
class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

if __name__ == "__main__":
    main()
