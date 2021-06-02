import os
from common import Log

class JobModel(object):
    
    def status(self, jobId):
        '''
            connect to ES DB and get the status of jobId
        '''
        log = Log.from_default()
        return log.get_status(jobId)