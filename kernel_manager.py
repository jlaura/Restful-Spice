from collections import OrderedDict
import glob
import os
import re


def create_kernel_listing():
    spice_root = '/data/spice/mess-e_v_h-spice-6-v1.0/messsp_1000/'
    meta_root =  os.path.join(spice_root, 'extras/mk')

    files = glob.glob(meta_root + '/*.tm')

    # Hard coded to Mercury, but easy enough to deal with applying this to any number of directories.
    meta = OrderedDict([])
    meta_kernels = {'mercury':{'messenger': meta}}
    for f in files:
        base = os.path.basename(f)
        base.split('_')
        _, year, version = base.split('_')
        meta.setdefault(year, []).append(base)
    for k, v in meta.items():
        sorted_meta = sorted(v, key=lambda x: re.search('v[0-9]+', x).group(), reverse=True)
        meta[k] = [os.path.join(meta_root, i) for i in sorted_meta]

    meta_kernels['mercury']['messenger'] = meta
    return meta_kernels
