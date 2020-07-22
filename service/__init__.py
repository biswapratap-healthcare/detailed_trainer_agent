from flask_cors import CORS
from flask import Flask

from flask_restplus import Resource, Api
from service.driver import run_d


def create_app():
    run_d()
    app = Flask(__name__, instance_relative_config=True)

    api = Api(
        app,
        version='1.0.0',
        title='Detailed Trainer Agent',
        description='Detailed Trainer Agent',
        default='Detailed Trainer Agent',
        default_label=''
    )

    CORS(app)

    @api.route('/hello')
    class Hello(Resource):
        def get(self):
            rv = dict()
            rv['Status'] = 'Ready'
            return rv, 200

    return app
