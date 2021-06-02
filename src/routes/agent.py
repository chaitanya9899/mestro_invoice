from flask import Blueprint
from flask_restful import Api

from resources import AgentRunResource,  AgentListResource , AgentInvoiceResource

AGENT_BLUEPRINT = Blueprint("agent", __name__)

Api(AGENT_BLUEPRINT).add_resource(
    AgentListResource, "/agent/v0/list"
)

Api(AGENT_BLUEPRINT).add_resource(
    AgentRunResource, "/agent/v0/run"
)

Api(AGENT_BLUEPRINT).add_resource(
    AgentInvoiceResource,"/agent/v0/invoice"
)
