
class AgentRunContext(object):

    def __init__(self,req):
        self.requestBody = req
        self.jobId = None
        self.homeURL = None
    
    @property
    def jobId(self):
        return self._jobId
    
    @jobId.setter
    def jobId(self,value):
        self._jobId = value
    
    @property
    def requestBody(self):
        return self._requestBody
    
    @requestBody.setter
    def requestBody(self,value):
        self._requestBody = value
    
    @property
    def homeURL(self):
        return self._homeURL
    
    @homeURL.setter
    def homeURL(self,value):
        self._homeURL = value