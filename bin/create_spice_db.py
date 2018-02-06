from sqlalchemy import Column, Integer, Boolean, String, Date
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from collections import OrderedDict
import datetime
import glob
import os
import re

# Cause I'm lazy
opj = os.path.join

from pfeffernusse.models import Base, Kernels, Missions

#TODO: Refactor this out via argparse or statically check for all PDS missions and allow additional
mission_dir_to_human_name = {'messsp_1000':'messenger',
                             'mrosp_1000':'mars_reconnaissance_orbiter',
                             'cosp_1000':'cassini'}
root = '/data/spice'

spice_roots = [os.path.join(root, 'mess-e_v_h-spice-6-v1.0/messsp_1000/'),
               os.path.join(root, 'mro-m-spice-6-v1.0/mrosp_1000/'),
               os.path.join(root, 'co-s_j_e_v-spice-6-v1.0/cosp_1000/')]


engine = create_engine('sqlite:///mk.db')
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()

def find_mk(spice_root):
    meta_root =  os.path.join(spice_root, 'extras/mk')

    files = glob.glob(meta_root + '/*.tm')

    # Hard coded to Mercury, but easy enough to deal with applying this to any number of directories.
    meta = OrderedDict([])
    for f in files:
        base = os.path.basename(f)
        base.split('_')
        _, year, version = base.split('_')
        try:
            year = int(year)
            meta.setdefault(year, []).append(base)
        except: pass

    for k, v in meta.items():
        sorted_meta = sorted(v, key=lambda x: re.search('v[0-9]+', x).group(), reverse=True)
        meta[k] = [os.path.join(meta_root, i) for i in sorted_meta]

    return meta

def find_kernels(spice_root):
    #TODO: Load all kernels into the database with .lbl files as JSON metadata
    data_root = os.path.join(spice_root, 'data')


data = {}
for data_dir in spice_roots:
    key = os.path.basename(os.path.normpath(data_dir))
    data[key] = find_mk(data_dir)

for mission, mks in data.items():
    metakernels = []
    mission = mission_dir_to_human_name[mission]
    mission = Missions(name=mission)

    for year, mk in mks.items():
        year = datetime.date(year, 1,1)
        for i, m in enumerate(mk):
            newest = False
            if i == 0:
                newest=True
            name = os.path.basename(os.path.normpath(m))
            metakernel = Kernels(mission=mission, name=name,
                              year=year, newest=newest,path=m)
            metakernels.append(metakernel)

        session.add_all(metakernels)
session.commit()
