import datetime
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from kernel_manager import create_kernel_listing
import create_isd
from utils import CustomJSONEncoder
from models import db, MetaKernels

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mk.db'
db.init_app(app)

csm_isd = {'messenger':{
             'mdis_nac': create_isd.isd_from_json,
             'mdis_wac': create_isd.isd_from_json,
             },
           'mars_reconnaissance_oribter':{
             'ctx': create_isd.ctx_isd_from_json,
             },
           'cassini':{
             'iss': create_isd.isd_from_json
              }
           }

@app.route('/')
def index():
    data = {'status':'success',
            'apis':{1.0:'api/1.0'}}
    return json.dumps(data, default=CustomJSONEncoder)

@app.route('/api/1.0/')
def api_description():
    resp = {'success':True, 'data':{}}
    data = resp['data']
    data['urls'] = {'missions': '/api/1.0/missions.'}
    return json.dumps(resp, default=CustomJSONEncoder)

@app.route('/api/1.0/missions/')
def missions():
    resp = {'success':True, 'data':{}}
    distinct = MetaKernels.query.with_entities(MetaKernels.mission).distinct().all()
    resp['data']['meta_kernels'] = [ d[0] for d in distinct ]
    return json.dumps(resp, default=CustomJSONEncoder)

@app.route('/api/1.0/missions/<mission>/')
def available_kernels(mission):
    resp = {'success':True, 'data':{}}
    data = resp['data']
    data['kernels'] = {'metakernels':'/api/1.0/missions/{}/metakernels'.format(mission)}
    return  json.dumps(resp, default=CustomJSONEncoder)

@app.route('/api/1.0/missions/<mission>/metakernels')
def available_meta_kernels(mission):
    resp = {'success':True, 'data':{}}
    data = resp['data']
    mission = mission.lower()
    kernels = MetaKernels.query.filter(MetaKernels.mission == mission).all()
    resp['data'] = [k.serialize for k in kernels]
    return json.dumps(resp, cls=CustomJSONEncoder)

@app.route('/api/1.0/missions/<mission>/<instrument>/csm_isd', methods=['GET', 'POST'])
def create_isd(mission, instrument):
    resp = {'success':True,
            'data':{}}
    if request.method == 'POST':
        data = request.get_json(force=True)
        mission = mission.lower()
        metakernels = MetaKernels.query.\
                       filter(MetaKernels.mission==mission).\
                       filter(MetaKernels.newest==True).\
                       with_entities(MetaKernels.path, MetaKernels.year).all()
        isd = csm_isd[mission][instrument](data, metakernels)
        resp['data']['isd'] = isd
        resp['data']['loaded_kernels'] = None
    else:
        resp['data'] = 0  # Get the mission specific post args
    return json.dumps(resp, cls=CustomJSONEncoder)

@app.route('/api/1.0/missions/<mission>/socet_set', methods=['GET', 'POST'])
def socet_set(mission):
    resp = {'success':True,
                'data':{}}
    if request.method == 'POST':
        data = request.get_json(force=True)
        #sset = my_func_to_create_a_set_as_json()
        sset = None
        resp['data']['set'] = sset
        resp['data']['loaded_kernels'] = None
    else:
        resp['data'] = 'POSTing to this endpoint will return a SOCET compliant .set file.'
    return jsonify(resp)



if __name__ == '__main__':
    app.response_failure = {'success':False, 'error_msg':""}
    app.json_encoder = CustomJSONEncoder
    app.run(port=5000, debug=True)
