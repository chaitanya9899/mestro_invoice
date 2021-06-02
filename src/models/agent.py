import os
import json

class AgentModel(object):
    def __init__(self):
        pass

    def get(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as json_file:
            try:
                data = json.load(json_file)
            except Exception as e:
                print('exception received: ', e)
                return None
            return data