from flask import Blueprint
from flask_restful import Api

from resources import JobStatusResource

JOB_BLUEPRINT = Blueprint("job", __name__)

Api(JOB_BLUEPRINT).add_resource(
    JobStatusResource, "/job/v0/status"
)
