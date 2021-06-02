from flask_restful import fields, marshal_with, reqparse, Resource
from flask import request
from repositories import JobRepo
from models import CustomResponse, Status
from app import basic_auth

import config

jobRepo   = JobRepo()

class JobStatusResource(Resource):
    @basic_auth.required
    def get(self):
        try:
            result = jobRepo.status(request.args.get('jobId'))
            if result != None:
                res = CustomResponse(Status.SUCCESS.value, result)
                return res.getres()
            else:
                res = CustomResponse(Status.ERR_GLOBAL_MISSING_PARAMETERS.value, None)
                return res.getresjson(), 400
        except Exception as e:
            print(e)
            res = CustomResponse(Status.ERR_GLOBAL_MISSING_PARAMETERS.value, None)
            return res.getresjson(), 400
