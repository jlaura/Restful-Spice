from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, String, Date
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from collections import OrderedDict
import datetime
import glob
import os
import re

from models import MetaKernels

mission_dir_to_human_name = {'messsp_1000':'MESSENGER',
                             'mrosp_1000':'Mars_Reconnaissance_Oribter',
                             'cosp_1000':'Cassini'}

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

root = '/data/spice'
opj = os.path.join
spice_roots = [opj(root, 'mess-e_v_h-spice-6-v1.0/messsp_1000/'),
               opj(root, 'mro-m-spice-6-v1.0/mrosp_1000/'),
               opj(root, 'co-s_j_e_v-spice-6-v1.0/cosp_1000/')]

data = {}
for data_dir in spice_roots:
    key = os.path.basename(os.path.normpath(data_dir))
    data[key] = find_mk(data_dir)

Base = declarative_base()

engine = create_engine('sqlite:///mk.db')

# Create the DB
Base.metadata.create_all(engine)

# Connect the session
Session = sessionmaker(bind=engine)
session = Session()

rows = []
for mission, mks in data.items():
    mission = mission_dir_to_human_name[mission]
    for year, mk in mks.items():
        year = datetime.date(year, 1,1)
        for i, m in enumerate(mk):
            newest = False
            if i == 0:
                newest=True
            name = os.path.basename(os.path.normpath(m))
            row = MetaKernels(mission=mission.lower(), name=name,
                              year=year, newest=newest,path=m)
            rows.append(row)
session.add_all(rows)
session.commit()
