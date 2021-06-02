import pickle
from .agent_class import Agent
import os

class AgentUtils:

    def __init__(self):
        self.filepath = None
    
    @property
    def filepath(self):
        return self._filepath
    
    @filepath.setter
    def filepath(self,value):
        self._filepath = value

    def __readPklFile(self):
        if os.path.exists(self.filepath):
            file_pi = open(self.filepath,'rb')
            agent_list = pickle.load(file_pi)
            return agent_list
        else:
            return []
    
    def __writePklFile(self,agent_list):
        file_pi = open(self.filepath,'wb')
        pickle.dump(agent_list,file_pi)
    
    def __get_agent(self,agentId):
        agent_list = self.__readPklFile()
        for i,agent in enumerate(agent_list):
            if agent.agentId == agentId:
                return agent,i
        raise ValueError("There is no agent with that agentId")
    
    def addAgent(self,agentId,description,energyProvider,agentScript,invoiceScript,homeURL):
        agent = Agent(agentId,description,energyProvider,agentScript,invoiceScript,homeURL)
        agent_list = self.__readPklFile()
        for old_agent in agent_list:
            if old_agent.agentId == agent.agentId:
                print('The agent already exists',agent)
                return
        agent_list.append(agent)
        self.__writePklFile(agent_list)
    
    def listAgents(self):
        return_list = []
        agent_list = self.__readPklFile()
        for old_agent in agent_list:
            agent = {}
            agent['agentId'] = old_agent.agentId
            agent['description'] = old_agent.description
            agent['energyProvider'] = old_agent.energyProvider
            agent['agentScript'] = old_agent.agentScript
            agent['invoiceScript'] = old_agent.invoiceScript
            agent['homeURL'] = old_agent.homeURL
            return_list.append(agent)
        return return_list
    
    def update_agentId(self,old_agentId,new_agentId):
        agent,_ = self.__get_agent(old_agentId)
        agent.agentId = new_agentId
    
    def update_energyProvider(self,agentId,energyProvider):
        agent,_ = self.__get_agent(agentId)
        agent.energyProvider = energyProvider

    def update_description(self,agentId,description):
        agent,_ = self.__get_agent(agentId)
        agent.description = description

    def update_script(self,agentId,script):
        agent,_ = self.__get_agent(agentId)
        agent.script = script

