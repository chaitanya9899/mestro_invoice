import config
from models import JobModel

class JobRepo:
    def __init__(self):
        self.jobModel = JobModel()
    
    def status(self, jobId):
        return self.jobModel.status(jobId)

    
