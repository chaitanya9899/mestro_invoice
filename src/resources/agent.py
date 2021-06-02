from flask_restful import fields, marshal_with, reqparse, Resource
from flask import request
from repositories import AgentRepo
from models import CustomResponse, Status
from utilities import AgentRunContext
import traceback

from app import basic_auth
import config
import os

from common import ValueMissing

agentRepo = AgentRepo()

def missing_param(req):
    param_list = []
    if req.get('agentId') is None:
        param_list.append('agentId')
    if req.get('username') is None:
        param_list.append('username')
    if req.get('password') is None:
        param_list.append('password')
    if len(param_list) > 0:
        return ",".join(param_list)
    else:
        return None


class AgentListResource(Resource):
    @basic_auth.required
    def get(self):
        try:
            result = agentRepo.list(os.path.join(config.APPLICATION_STATIC_PATH, config.AGENT_CONFIG_PKL_FILEPATH))
            if result != None:
                res = CustomResponse(Status.SUCCESS.value, result)
                return res.getres()
            else:
                res = CustomResponse(Status.ERR_GLOBAL_MISSING_PARAMETERS.value, None)
                return res.getresjson(), 400
        except Exception:
            res = CustomResponse(Status.ERR_GLOBAL_MISSING_PARAMETERS.value, None)
            return res.getresjson(), 400

class AgentRunResource(Resource):
    @basic_auth.required
    def post(self):
        try:
            req = request.get_json()
            miss = missing_param(req)
            if miss is not None:
                raise ValueMissing(miss+' - mandatory')
            agentRunContext = AgentRunContext(req)
            result = agentRepo.run(agentRunContext,os.path.join(config.APPLICATION_STATIC_PATH, config.AGENT_CONFIG_PKL_FILEPATH))
            if result != None:
                res = CustomResponse(Status.SUCCESS.value, result)
                return res.getres()
            else:
                res = CustomResponse(Status.ERR_GLOBAL_INVALID_AGENT_ID.value, None)
                return res.getresjson(), 400
        except Exception as e:
            res = CustomResponse(Status.ERR_GLOBAL_MISSING_PARAMETERS.value,str(e))
            return res.getresjson(),400

class AgentInvoiceResource(Resource):
    @basic_auth.required
    def post(self):
        try:
            req = request.get_json()
            miss = missing_param(req)
            if miss is not None:
                raise ValueMissing(miss+' - mandatory')
            agentRunContext = AgentRunContext(req)
            result = agentRepo.invoice(agentRunContext,os.path.join(config.APPLICATION_STATIC_PATH, config.AGENT_CONFIG_PKL_FILEPATH))
            if result != None:
                res = CustomResponse(Status.SUCCESS.value, result)
                return res.getres()
            else:
                res = CustomResponse(Status.ERR_GLOBAL_INVALID_AGENT_ID.value, None)
                return res.getresjson(), 400
        except Exception as e:
            res = CustomResponse(Status.ERR_GLOBAL_MISSING_PARAMETERS.value,str(e))
            return res.getresjson(),400

