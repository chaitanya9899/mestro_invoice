class Agent(object):
    def __init__(self,agentId,description,energyProvider,agentScript,invoiceScript,homeURL):
        self.energyProvider = energyProvider
        self.description = description
        self.agentId = agentId
        self.agentScript = agentScript
        self.invoiceScript = invoiceScript
        self.homeURL = homeURL
    
    @property
    def agentId(self):
        return self._agentId
    
    @agentId.setter
    def agentId(self,value):
        self._agentId = value
    
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self,value):
        self._description = value

    @property
    def energyProvider(self):
        return self._energyProvider
    
    @energyProvider.setter
    def energyProvider(self,value):
        self._energyProvider = value

    @property
    def agentScript(self):
        return self._agentScript
    
    @agentScript.setter
    def agentScript(self,value):
        self._agentScript = value
    
    @property
    def invoiceScript(self):
        return self._invoiceScript
    
    @invoiceScript.setter
    def invoiceScript(self,value):
        self._invoiceScript = value
    
    @property
    def homeURL(self):
        return self._homeURL
    
    @homeURL.setter
    def homeURL(self,value):
        self._homeURL = value
    
    def __str__(self):
        return 'id: {0} , description: {1} , energyProvider: {2} , agentScript: {3} , invoiceScript: {4} , homeURL: {5}'.format(self.agentId,self.description,self.energyProvider,self.agentScript,self.invoiceScript,self.homeURL)