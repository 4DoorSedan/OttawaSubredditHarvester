import time

#TO DO
#It appears that there the captureReplies() method is called it is returning a legitmeate reply and then an empyt list
#this means that by the end of the recurisive call all of the returned comments are being spaced apart by an empty list
#To reporduce -> Hit it at the breakpoint and then step through a single time and look at the elements being applied to the list

class commentFactory:
    """
    Factory class reponsible for the creation of comment objects of three types
    titleComment -> This class represents the post as a comment    
    bodyComment -> This class represents a top level comment that is in reply to the post
    replyComment -> This class represents a comment that was in reply to another comment
    """

    #This is the factory method that will construct the required comment class bassed upon the type argument
    @classmethod
    def createComment(self, type, data, par_id=""):
        """Factory Method"""
        if type == "bodyComment":
            return bodyComment(data, par_id)
        elif type == "replyComment":
            return replyComment(data, par_id)
        elif type == "titleComment":
            return replyComment(data, par_id)
        else:
            raise TypeError #This should probably be a different kind of error

"""
Abstract class that is only used as a parent class for the three comment classes. Calling the methods of this class will not work
"""
class comment:
        #Data Variables
        _dataKeys = [
                "author", "author_flair_css_class", "author_flair_text", "ups", "downs", "score", "total_awards_received", "id", "body", "created_utc"
        ]

        def dateofcreation_localtime(self):
            if isinstance(self, (replyComment, bodyComment, titleComment)):
                return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._commentData["created_utc"]))
            else:
                raise NotImplementedError

        def getcommentId(self):
            if isinstance(self, (replyComment, bodyComment, titleComment)):
                return self._commentId["id"]
            else:
                raise NotImplementedError

        def getparentId(self):
            if isinstance(self, (bodyComment, replyComment)):
                return self._commentData["parent_id"]
            else:
                raise NotImplementedError
                #Should probably push something to the logger here

        #Recursive function that captures all of the comments attachted to another. Should be called only for the top comments
        def _createChildrenComments(self, childrenData):
            if isinstance(self, (bodyComment, replyComment)):
                dataList = []   
                for child in childrenData:    #Data will be passed in as a list
                    reply = commentFactory.createComment("replyComment", child["data"], self._commentData["id"])
                    if self._commentData["replyData"] == "":
                        dataList.append(reply)
                    else:
                        dataList.append(reply)
                        dataList.append(reply.captureReplies())
                return dataList
            else:
                raise NotImplementedError

class bodyComment(comment):
    
        def __init__(self, data: dict, parent_id):
            self._commentData = {}
            self._commentData["parent_id"] = parent_id
            self._commentData["isReply"] = False
            if data["replies"] != "":
                self._commentData["replyData"] = data["replies"]["data"]["children"]
            else:
                self._commentData["replyData"] = data["replies"]
            for key in self._dataKeys: #Copy data over to the class
                self._commentData[key] = data[key]

        def captureReplies(self):
            replies = []
            for com in self._createChildrenComments(self._commentData["replyData"]):
                replies.append(com)
            return replies

class replyComment(comment):
        def __init__(self, data: dict, parent_id):
            self._commentData = {}
            self._commentData["parent_id"] = parent_id
            self._commentData["isReply"] = True
            if data["replies"] != "":
                self._commentData["replyData"] = data["replies"]["data"]["children"]
            else:
                self._commentData["replyData"] = ""
            for key in self._dataKeys: #Copy data over to the class
                self._commentData[key] = data[key]

        def captureReplies(self):
            replies = []
            replies.append(self._createChildrenComments(self._commentData["replyData"]))
            return replies

class titleComment(comment):
        def __init__(self, data: dict, parent_id):
            self._commentData = {}
            self._commentData["parent_id"] = data["id"]
            self._commentData["isReply"] = False
            self._commentData["replyData"] = data["replies"]["data"]["children"]
            for key in self._dataKeys: #Copy data over to the class
                self._commentData[key] = data[key]

def testClass():
    import requests
    import json

    response = requests.get("https://www.reddit.com/r/ottawa/comments/o9m1kh/keep_your_agitprop_off_my_car/.json", headers={"User-agent" : "yourbot"}, timeout=120)
    rawData = response.json()
    comments = rawData[1]["data"]["children"]
    listofComments = []
    parentId = None
    commentFact = commentFactory()
    for index, item in enumerate(comments):
        if index == 0:
            comment = commentFact.createComment("titleComment", item["data"])
            parentId = comment.getparentId()
            listofComments.append(comment)
        else:
            comment = commentFact.createComment("bodyComment", item["data"], parentId)
            listofComments.append(comment)
    for com in listofComments:
        if isinstance(com, bodyComment) & (com._commentData["replyData"] != ""):
                for reply in com.captureReplies():
                    listofComments.append(reply)
    for com in listofComments:
        print(com.getcommentId())

#Test part of script 
if __name__ == "__main__":
    testClass()
