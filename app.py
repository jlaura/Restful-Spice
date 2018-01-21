import datetime
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from kernel_manager import create_kernel_listing
import create_isd
from utils import NumpyAwareJSONEncoder


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mk.db'
db = SQLAlchemy(app)

class MetaKernels(db.Model):
    __tablename__='metakernels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    newest = db.Column(db.Boolean)
    path = db.Column(db.String)
    year = db.Column(db.Date)
    mission = db.Column(db.String)

    def __repr__(self):
        return "id: {}, name:{}, newest:{}, path:{}, year:{}, mission: {}".format(self.id,
                self.name, self.newest, self.path, self.year, self.mission)

csm_isd = {'messenger':{
             'mdis_nac': create_isd.mdis_isd_from_json,
             'mdis_wac': create_isd.mdis_isd_from_json,
           },
           'mars_reconnaissance_oribter':{
             'ctx': create_isd.ctx_isd_from_json,
           }}

@app.route('/')
def index():
    data = {'status':'success',
            'apis':{1.0:'api/1.0'}}
    return jsonify(data)

@app.route('/api/1.0/csm_isd', methods=['GET', 'POST'])
def generate_isd():
    resp = {'success':True,
                'data':{}}
    if request.method == 'POST':
        data = request.get_json(force=True)
        isd = isd_from_json(data, app.meta_kernels)
        resp['data']['isd'] = isd
        resp['data']['loaded_kernels'] = None
    else:
        resp['data'] = 'Describe this end point'
    return jsonify(resp)

@app.route('/api/1.0')
def api_description():
    resp = {'success':True, 'data':{}}
    data = resp['data']
    data['available_missions'] = {'mercury':{'messenger': '/api/1.0/mercury/messenger'}}
    return jsonify(resp)

@app.route('/api/1.0/missions/')
def missions():
    resp = {'success':True, 'data':{}}
    distinct = MetaKernels.query.with_entities(MetaKernels.mission).distinct().all()
    resp['data']['meta_kernels'] = distinct
    return jsonify(resp)

@app.route('/api/1.0/missions/<mission>/')
def available_kernels(mission):
    resp = {'success':True, 'data':{}}
    data = resp['data']
    mission = mission.lower()
    kernels = MetaKernels.query.filter(MetaKernels.mission == mission).all()
    print(kernels)
    data['kernels'] = kernels
    data['description'] = "All available meta kernels for a given body and mission in sorted order.  The first meta kernel in the list will be loaded unless a different metakernel is specified."
    return  json.dumps(resp, default=alchemyencoder)

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
    return jsonify(resp)

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
    #app.json_encoder = NumpyAwareJSONEncoder
    app.response_failure = {'success':False, 'error_msg':""}
    app.run(host="0.0.0.0", debug=True, processes=6)
