from flask import Flask
from flask.blueprints import Blueprint
from flask_cors import CORS
from flask_basicauth import BasicAuth
import routes
import config
from models import AgentUtils
from crawler_scripts import UmeaEnergi
import os
import json
import sys

server      = Flask(__name__)
config.APPLICATION_STATIC_PATH  = server.static_folder

server.config['BASIC_AUTH_USERNAME'] = config.BASIC_HTTP_USERAME
server.config['BASIC_AUTH_PASSWORD'] = config.BASIC_HTTP_PASSWORD

basic_auth = BasicAuth(server)

with open(os.path.join(config.APPLICATION_STATIC_PATH,config.AGENT_CONFIG_FILEPATH),'r') as f:
    agent_list = json.load(f)

__import__("crawler_scripts")
__import__("invoice_scripts")
crawler_scripts = sys.modules["crawler_scripts"]
invoice_scripts = sys.modules["invoice_scripts"]

agentUtils = AgentUtils()
agentUtils.filepath = os.path.join(config.APPLICATION_STATIC_PATH,config.AGENT_CONFIG_PKL_FILEPATH)
pkl_agent_list = agentUtils.listAgents()
len_diff = len(agent_list) - len(pkl_agent_list)
for i in range(len(agent_list)-1,len(agent_list)-len_diff-1,-1):
    agent = agent_list[i]
    # print(agent)
    agentUtils.addAgent(agent['agentId'],agent['description'],agent['energyProvider'],crawler_scripts.__dict__[agent['agentScript']],invoice_scripts.__dict__[agent['invoiceScript']],agent['homeURL'])



if config.ENABLE_CORS:
    cors    = CORS(server, resources={r"/api/*": {"origins": "*"}})

for blueprint in vars(routes).values():
    if isinstance(blueprint, Blueprint):
        server.register_blueprint(blueprint, url_prefix=config.API_URL_PREFIX)

@server.route('/')
def home():
    return "<h1>HI</h1>"

if __name__ == "__main__":
    print('starting server at {} at port {}'.format(config.HOST, config.PORT))
    
    server.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)
