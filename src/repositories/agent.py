import config
from models import AgentUtils
import uuid
import json
import os
from threading import Thread

class AgentRepo:
    def __init__(self):
        self.agentUtils = AgentUtils()

    def list(self,filepath):
        self.agentUtils.filepath = filepath
        result = self.agentUtils.listAgents()
        for agent in result:
            agent.pop('agentScript')
            agent.pop('invoiceScript')
        return result

    def run(self, agentRunContext,filepath):
        jobId = str(uuid.uuid4())
        agentRunContext.jobId = jobId
        self.agentUtils.filepath = filepath
        agents_list = self.agentUtils.listAgents()
        threadStarted = False
        for agent in agents_list:
            if agent['agentId'] == agentRunContext.requestBody['agentId']:
                threadStarted = True
                agentRunContext.homeURL = agent['homeURL']
                thread = Thread(target=agent['agentScript'],args=(agentRunContext,))
                thread.start()
        if threadStarted:
            return {'jobId':jobId}
        else:
            return None
    
    def invoice(self,agentRunContext,filepath):
        jobId = str(uuid.uuid4())
        agentRunContext.jobId = jobId
        self.agentUtils.filepath = filepath
        agents_list = self.agentUtils.listAgents()
        threadStarted = False
        for agent in agents_list:
            if agent['agentId'] == agentRunContext.requestBody['agentId']:
                agentRunContext.homeURL = agent['homeURL']
                threadStarted = True
                thread = Thread(target=agent['invoiceScript'],args=(agentRunContext,))
                thread.start()
        if threadStarted:
            return {'jobId':jobId}
        else:
            return None

