import datetime
import decimal
from json import JSONEncoder
import numpy as np

def distort_focal_length(coeffs, t):
    """
    Compute the distorted focal length

    Parameters
    ----------
    coeffs : iterable
             of coefficient values
    t : float
        temperature in C

    Returns
    -------
    focal_length : float
                   the temperature adjusted focal length
    """
    focal_length = coeffs[0]
    for i in range(1, len(coeffs[1:])):
        focal_length += coeffs[i]*t**i
    return focal_length


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, np.ndarray) and obj.ndim == 1:
            lobj = obj.tolist()
            if len(lobj) == 1:
                return lobj[0]
            else:
                return lobj


        return JSONEncoder.default(self, obj)
