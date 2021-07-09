#This class works as an way for another script to pull all of the comments off of a reddit post
#This comments will be returned in list form and made up of the classes in the "RedditComment.py" file

import RedditComment
import requests
import logging

class commentPuller:
    commentPullerLogger = logging.getLogger("Comment Puller")

    def __init__(self, postURL : str):
        #Class variables
        self._postURL = postURL
        self._listofComments = []
        #End of class variables
        self.pullComments()
    #end of __init__ function
    
    def pullComments(self):
        response = None
        try:
            response =  requests.get(self._postURL+".json",headers={"User-agent" : "yourbot"}, timeout=60)
        except TimeoutError: #A timeout error will result in an empty list being returned
            self.commentPullerLogger.error("TimeOut error getting comment with the URL: %")%(self._postURL)
            return []
        response=response.json()
        self.postID = response[0]["data"]["children"][0]["data"]["id"]
        rawComments = response[1]["data"]["children"] #This will set response to be the list of comments in the json file
        comFactory = RedditComment.commentFactory
        for comData in rawComments:
            if comData["kind"] == "t3":
                comment = comFactory.createComment("titleComment", comData["data"])
                self._listofComments.append(comment)
            else:
                comment = comFactory.createComment("bodyComment", comData["data"], self.postID)
                self._listofComments.append(comment)
        for com in self._listofComments:
            if isinstance(com, RedditComment.bodyComment)|isinstance(com, RedditComment.replyComment) & (com._commentData["replyData"] != ""):
                for reply in com.captureReplies():
                    self._listofComments.append(reply)

    def comments(self):
        return self._listofComments

if __name__ == "__main__":
    comments = commentPuller("https://www.reddit.com/r/ottawa/comments/o9m1kh/keep_your_agitprop_off_my_car/.json")
    print(comments.comments())


        
