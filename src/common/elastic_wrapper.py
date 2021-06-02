import config
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import json
import time

class Log(object):

    @classmethod
    def from_default(cls):
        return cls(None)

    def __init__(self,agentRunContext):
        self.agentRunContext = agentRunContext
        self.es_client = Elasticsearch([config.ELASTIC_DB_URL])
    
    def __populate_context(self):
        data = {
            'agentId':self.agentRunContext.requestBody['agentId'],
            'jobId':self.agentRunContext.jobId,
            'username':self.agentRunContext.requestBody['username'],
            'timestamp':int(time.time()*1000),
            'password':self.agentRunContext.requestBody['password']
        }
        return data
    
    def __index_data_to_es(self,index,data):
        if self.es_client.ping():
            self.es_client.index(index=index,body=json.dumps(data))
        else:
            with open('logger.txt','a+') as f:
                f.write(json.dumps(data)+'\n')
    
    #log_data = {
    # 'agentId':'',
    # 'jobId':'',
    # 'username':'',
    # 'type':'info/error/exception',
    # 'message':'',
    # 'timestamp':''
    # }
    def error(self,error_message):
        error_data = self.__populate_context()
        error_data['type'] = 'error'
        error_data['message'] = error_message
        self.__index_data_to_es(config.ES_LOG_INDEX,error_data)

    def info(self,message):
        info_data = self.__populate_context()
        info_data['type'] = 'info'
        info_data['message'] = message
        self.__index_data_to_es(config.ES_LOG_INDEX,info_data)
    
    def exception(self,exception_message):
        exception_data = self.__populate_context()
        exception_data['type'] = 'exception'
        exception_data['message'] = exception_message
        self.__index_data_to_es(config.ES_LOG_INDEX,exception_data)
    
    #crawl_data = {
    # '_index':'',
    # 'agentId':'',
    # 'jobId':'',
    # 'username':'',
    # 'facilityId':'',
    # 'kind':'',
    # 'quantity':'',
    # 'startDate':,
    # 'endDate':'',
    # 'value':'',
    # 'unit':'kWh',
    # 'timestamp':''
    # }
    def data(self,complete_data):
        for data in complete_data:
            data['_index'] = config.ES_DATA_INDEX_2
            data.update(self.__populate_context())
        bulk(self.es_client,complete_data)

    #job_data = {
    # 'agentId':'',
    # 'jobId':'',
    # 'username':'',
    # 'message':'',
    # 'status':'',
    # 'timestamp':''
    # }
    def job(self,status,message):
        job_data = self.__populate_context()
        job_data['status'] = status
        job_data['message'] = message
        self.__index_data_to_es(config.ES_JOB_INDEX,job_data)
    
    def get_status(self,jobId):
        if not self.es_client.ping():
            with open('logger.txt','a+') as f:
                f.write(jobId+': Not able to connect to ES DB\n')
            return None
        else:
            search_param = {
            "sort": [
                {
                "timestamp": {
                    "order": "desc"
                }
                }
            ], 
            "query": {
                "bool": {
                "must": [
                    {"match": {
                    "jobId": jobId
                    }}
                ]
                }
            }
            }

            res = self.es_client.search(index=config.ES_JOB_INDEX,body=search_param)

            source = res['hits']['hits'][0]['_source']
            
            return {'status':source['status'],'message':source['message']}

