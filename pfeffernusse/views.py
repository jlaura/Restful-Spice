from flask import jsonify, request, Blueprint

from pfeffernusse import create_isd
from pfeffernusse.models import db, Kernels, Missions

api = Blueprint('api', __name__)

# TODO: Handle instrument dispatching internally
csm_isd = {'messenger':create_isd.isd_from_json,
           'mars_reconnaissance_oribter':create_isd.ctx_isd_from_json,
           'cassini':create_isd.isd_from_json
           }

@api.route('/')
@api.route('/index.html')
def index():
    data = {'status':'success',
            'apis':{1.0:'api/1.0'}}
    return jsonify(data)

@api.route('/1.0/')
def api_description():
    resp = {'success':True, 'data':{}}
    data = resp['data']
    data['urls'] = {'missions': '/api/1.0/missions.'}
    return jsonify(resp)

@api.route('/1.0/missions/')
def missions():
    resp = {'success':True, 'data':{}}
    missions = db.session.query(Missions).all()
    resp['missions'] = [ m.serialize for m in missions ]
    return jsonify(resp)

@api.route('/1.0/missions/<mission>/')
def available_kernels(mission):
    resp = {'success':True, 'data':{}}
    data = resp['data']
    data['kernels'] = {'metakernels':'/api/1.0/missions/{}/metakernels'.format(mission)}
    return jsonify(resp)

@api.route('/1.0/missions/<mission>/kernels')
def available_kernels_by_mission(mission):
    resp = {'success':True, 'data':{}}
    data = resp['data']
    mission = mission.lower()
    kernels = db.session.query(Kernels).filter(Missions.name == mission).all()
    resp['data'] = [k.serialize for k in kernels]
    return jsonify(resp)

@api.route('/1.0/missions/<mission>/kernels/<type_name>')
def kernels_by_type(mission, type_name):
    pass

@api.route('/1.0/missions/<mission>/csm_isd')
def create_isd(mission):
    resp = {'success':True,
            'data':{}}
    if request.method == 'POST':
        data = request.get_json(force=True)
        mission = mission.lower()
        metakernels = db.session.query(Kernels).\
                       filter(Kernels.mission==mission).\
                       filter(Kernels.newest==True).\
                       with_entities(Kernels.path, Kernels.year).all()
        isd = csm_isd[mission][instrument](data, metakernels)
        resp['data']['isd'] = isd
        resp['data']['loaded_kernels'] = None
    else:
        resp['data'] = 0  # Get the mission specific post args
    return jsonify(resp)

@api.route('/1.0/missions/<mission>/socet_set', methods=['GET', 'POST'])
def socet_set(mission):
    resp = {'success':True,
                'data':{}}
    if request.method == 'POST':
        data = request.get_json(force=True)
        sset = None
        resp['data']['set'] = sset
        resp['data']['loaded_kernels'] = None
    else:
        resp['data'] = 'POSTing to this endpoint will return a SOCET compliant .set file.'
    return jsonify(resp)
