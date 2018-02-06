from dateutil import parser
from math import sqrt
import os
import glob
import numpy as np
import spiceypy as spice

from pfeffernusse.utils import distort_focal_length
import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

# Utility Func for working with PVL
def find_in_dict(obj, key):
    """
    Recursively find an entry in a dictionary

    Parameters
    ----------
    obj : dict
          The dictionary to search
    key : str
          The key to find in the dictionary

    Returns
    -------
    item : obj
           The value from the dictionary
    """
    if key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = find_in_dict(v, key)
            if item is not None:
                return item

def isd_from_json(data, meta):
    instrument_name = {'IMAGING SCIENCE SUBSYSTEM NARROW ANGLE': 'CASSINI_ISS_NAC',
                       'IMAGING SCIENCE SUBSYSTEM WIDE ANGLE': 'CASSINI_ISS_WAC',
                       'IMAGING SCIENCE SUBSYSTEM - NARROW ANGLE': 'CASSINI_ISS_NAC',
                       'MDIS-NAC':'MSGR_MDIS_NAC',
                       'MERCURY DUAL IMAGING SYSTEM NARROW ANGLE CAMERA':'MSGR_MDIS_NAC',
                       'MERCURY DUAL IMAGING SYSTEM WIDE ANGLE CAMERA':'MSGR_MDIS_WAC'}

    spacecraft_names = {'CASSINI ORBITER': 'CASSINI',
                        'MESSENGER': 'MESSENGER'}


    # This is the return dict
    isd = {}

    # Meta kernels are keyed by body, spacecraft, and year - grab from the data
    spacecraft_name = spacecraft_names[data['spacecraft_id']]
    target_name = data['target_name']
    time = parser.parse(data['capture_date'])

    for k in meta:
        if k.year.year == time.year:
            obs_kernels = k.path

    # Load the meta kernel
    spice.furnsh(obs_kernels)
    path, tpe, handle, found = spice.kdata(0,'TEXT')
    if not found:
        directory = os.path.dirname(path)
        directory = os.path.abspath(os.path.join(directory, '../iak'))
        additional_ik = glob.glob(directory + '/*.ti')
        spice.furnsh(additional_ik)

    # Spice likes ids over names, so grab the ids from the names
    instrument_name = instrument_name[data['instrument']]
    spacecraft_id = spice.bods2c(spacecraft_name)
    ikid = spice.bods2c(instrument_name)

    # Load the instrument and target metadata into the ISD
    isd['instrument_id'] = instrument_name
    isd['target_name'] = target_name
    isd['spacecraft_name'] = spacecraft_name

    # Prepend IAU to all instances of the body name
    reference_frame = 'IAU_{}'.format(target_name)

    # Load information from the IK kernel
    isd['focal_length'] = spice.gdpool('INS{}_FOCAL_LENGTH'.format(ikid), 0, 1)
    isd['focal_length_epsilon'] = spice.gdpool('INS{}_FL_UNCERTAINTY'.format(ikid), 0, 1)
    isd['nlines'] = spice.gipool('INS{}_PIXEL_LINES'.format(ikid), 0, 1)
    isd['nsamples'] = spice.gipool('INS{}_PIXEL_SAMPLES'.format(ikid), 0, 1)
    isd['original_half_lines'] = isd['nlines'] / 2.0
    isd['original_half_samples'] = isd['nsamples'] / 2.0
    isd['pixel_pitch'] = spice.gdpool('INS{}_PIXEL_PITCH'.format(ikid), 0, 1)
    isd['ccd_center'] = spice.gdpool('INS{}_CCD_CENTER'.format(ikid), 0, 2)
    isd['ifov'] = spice.gdpool('INS{}_IFOV'.format(ikid), 0, 1)
    isd['boresight'] = spice.gdpool('INS{}_BORESIGHT'.format(ikid), 0, 3)
    isd['transx'] = spice.gdpool('INS{}_TRANSX'.format(ikid), 0, 3)
    isd['transy'] = spice.gdpool('INS{}_TRANSY'.format(ikid), 0, 3)
    isd['itrans_sample'] = spice.gdpool('INS{}_ITRANSS'.format(ikid), 0, 3)
    isd['itrans_line'] = spice.gdpool('INS{}_ITRANSL'.format(ikid), 0, 3)
    try:
        isd['odt_x'] = spice.gdpool('INS-{}_OD_T_X'.format(ikid), 0, 10)
    except:
        isd['odt_x'] = np.zeros(10)
        isd['odt_x'][1] = 1
    try:
        isd['odt_y'] = spice.gdpool('INS-{}_OD_T_Y'.format(ikid), 0, 10)
    except:
        isd['odt_y'] = np.zeros(10)
        isd['odt_y'][2] = 1
    try:
        isd['starting_detector_sample'] = spice.gdpool('INS{}_FPUBIN_START_SAMPLE'.format(ikid), 0, 1)
    except:
        isd['starting_detector_sample'] = 0
    try:
        isd['starting_detector_line'] = spice.gdpool('INS{}_FPUBIN_START_LINE'.format(ikid), 0, 1)
    except:
        isd['starting_detector_line'] = 0

    # Get temperature from SPICE and adjust focal length
    if 'focal_plane_temperature' in data.keys():
        try:  # TODO: Remove once WAC temperature dependent is working
            temp_coeffs = spice.gdpool('INS-{}_FL_TEMP_COEFFS'.format(ikid), 0, 6)
            temp = data['focal_plane_temperature']
            isd['focal_length'] = distort_focal_length(temp_coeffs, temp)
        except:
            isd['focal_length'] = spice.gdpool('INS-{}_FOCAL_LENGTH'.format(ikid), 0, 1)
    else:
        isd['focal_length'] = spice.gdpool('INS-{}_FOCAL_LENGTH'.format(ikid), 0, 1)

    # Get the radii from SPICE
    rad = spice.bodvrd(isd['target_name'], 'RADII', 3)
    radii = rad[1]
    isd['semi_major_axis'] = rad[1][0]
    isd['semi_minor_axis'] = rad[1][1]

    # Now time
    sclock = data['spacecraft_clock_count']
    exposure_duration = data['exposure_duration']
    exposure_duration = exposure_duration * 0.001  # Scale to seconds


    # Get the instrument id, and, since this is a framer, set the time to the middle of the exposure
    et = spice.scs2e(spacecraft_id, sclock)
    et += (exposure_duration / 2.0)

    isd['ephemeris_time'] = et

    # Get the Sensor Position
    loc, _ = spice.spkpos(isd['target_name'], et, reference_frame, 'LT+S', spacecraft_name)
    loc *= -1000
    isd['x_sensor_origin'] = loc[0]
    isd['y_sensor_origin'] = loc[1]
    isd['z_sensor_origin'] = loc[2]

    # Get the rotation angles from MDIS NAC frame to Mercury body-fixed frame
    camera2bodyfixed = spice.pxform(instrument_name,reference_frame,et)
    opk = spice.m2eul(camera2bodyfixed, 3, 2, 1)

    isd['omega'] = opk[2]
    isd['phi'] = opk[1]
    isd['kappa'] = opk[0]

    # Get the sun position
    sun_state, lt = spice.spkezr("SUN",
                             et,
                             reference_frame,
                             data['lighttime_correction'],
                             target_name)

    # Convert to meters
    isd['x_sun_position'] = sun_state[0] * 1000
    isd['y_sun_position'] = sun_state[1] * 1000
    isd['z_sun_position'] = sun_state[2] * 1000

    # Get the velocity
    v_state, lt = spice.spkezr(spacecraft_name,
                                       et,
                                       reference_frame,
                                       data['lighttime_correction'],
                                       target_name)

    isd['x_sensor_velocity'] = v_state[3] * 1000
    isd['y_sensor_velocity'] = v_state[4] * 1000
    isd['z_sensor_velocity'] = v_state[5] * 1000


    # Misc. insertion
    # A lookup here would be smart - similar to the meta kernals, what is the newest model, etc.
    if 'model_name' not in data.keys():
        isd['model_name'] = 'ISIS_MDISNAC_USGSAstro_1_Linux64_csm30.so'
    isd['min_elevation'] = data['min_elevation']
    isd['max_elevation'] = data['max_elevation']


    spice.unload(obs_kernels)  # Also unload iak
    return isd

def ctx_isd_from_json(data, meta):
    time = parser.parse(data['START_TIME'])
    for k in meta:
        if k.year.year == time.year:
            obs_kernels = k.path

    # Load the meta kernel
    spice.furnsh(obs_kernels)


    isd = {}
    spacecraft_name = data['SPACECRAFT_NAME']
    spacecraft_id = spice.bods2c('MRO')

    # Need to map CONTEXT CAMERA to what spice wants - MRO_CTX
    instrument_name = data['INSTRUMENT_NAME']
    ikid = isd['IKCODE'] = spice.bods2c('MRO_CTX')

    # Instrument / Spacecraft Metadata
    isd['OPTICAL_DIST_COEF'] = spice.gdpool('INS{}_OD_K'.format(ikid),0, 3)
    isd['ITRANSL'] = spice.gdpool('INS{}_ITRANSL'.format(ikid), 0, 3)
    isd['ITRANSS'] = spice.gdpool('INS{}_ITRANSS'.format(ikid), 0, 3)
    isd['DETECTOR_SAMPLE_ORIGIN'] = spice.gdpool('INS{}_BORESIGHT_SAMPLE'.format(ikid), 0, 1)
    isd['DETECTOR_LINE_ORIGIN'] = spice.gdpool('INS{}_BORESIGHT_LINE'.format(ikid), 0, 1)
    isd['DETECTOR_SAMPLE_SUMMING'] = data['SAMPLING_FACTOR']
    isd['DETECTOR_SAMPLE_SUMMING'] = data['SAMPLING_FACTOR']
    isd['STARTING_SAMPLE'] = data['SAMPLE_FIRST_PIXEL']
    isd['TOTAL_LINES'] = nlines =  data['IMAGE']['LINES']
    isd['TOTAL_SAMPLES'] = spice.gdpool('INS{}_PIXEL_SAMPLES'.format(ikid), 0, 1)
    isd['SENSOR_TYPE'] = 'USGSAstroLineScanner'
    isd['MOUNTING_ANGLES'] = np.zeros(3)
    isd['ISIS_Z_DIRECTION'] = 1
    isd['STARTING_LINE'] = 1.0
    isd['DETECTOR_LINE_OFFSET'] = 0.0

    # Body Parameters
    target_name = find_in_dict(data, 'TARGET_NAME')
    rad = spice.bodvrd(target_name, 'RADII', 3)
    a = rad[1][1]
    b = rad[1][2]
    isd['SEMI_MAJOR_AXIS'] = a * 1000  # Scale to meters
    isd['ECCENTRICITY'] = sqrt(1 - (b**2 / a**2)) # Standard eccentricity

    isd['FOCAL'] = spice.gdpool('INS{}_FOCAL_LENGTH'.format(ikid), 0, 1)

    isd['ABERR'] = 0
    isd['ATMREF'] = 0
    isd['PLATFORM'] = 1

    # It really is hard coded this way...
    isd['TRI_PARAMETERS'] = np.zeros(18)
    isd['TRI_PARAMETERS'][15] = isd['FOCAL']

    # Time
    sclock = find_in_dict(data, 'SPACECRAFT_CLOCK_START_COUNT')
    et = spice.scs2e(spacecraft_id, sclock)
    isd['STARTING_EPHEMERIS_TIME'] = et

    half_lines = nlines / 2
    isd['INT_TIME'] = line_rate = data['LINE_EXPOSURE_DURATION'][0] * 0.001  # Scale to seconds
    center_sclock = et + half_lines * line_rate
    isd['CENTER_EPHEMERIS_TIME'] = center_sclock
    isd['SCAN_DURATION'] = line_rate * nlines
    # The socetlinekeywords code is pushing ephemeris and quaternion off of either side of the image.  Therefore,
    # the code needs to know when the start time is.  Since we are not pushing off the edge of the image, the start-time
    # should be identical to the actual image start time.
    isd['T0_QUAT'] = isd['T0_EPHEM'] = isd['STARTING_EPHEMERIS_TIME'] - isd['CENTER_EPHEMERIS_TIME']
    isd['DT_EPHEM'] = 80 * isd['INT_TIME']  # This is every 300 lines

    # Determine how many ephemeris points to compute
    n_ephemeris = int(isd['SCAN_DURATION'] / isd['DT_EPHEM'])
    if n_ephemeris % 2 == 0:
        n_ephemeris += 1
    isd['NUMBER_OF_EPHEM'] = n_ephemeris
    eph = np.empty((n_ephemeris, 3))
    eph_rates = np.empty(eph.shape)
    current_et = et
    for i in range(n_ephemeris):
        loc_direct, _ = spice.spkpos(target_name, current_et, 'IAU_MARS', 'LT+S', 'MRO')
        state, _ = spice.spkezr(target_name, current_et, 'IAU_MARS', 'LT+S', 'MRO')
        eph[i] = loc_direct
        eph_rates[i] = state[3:]
        current_et += isd['DT_EPHEM'] # Increment the time by the number of lines being stepped
    eph *= -1000 # Reverse to be from body center and convert to meters
    eph_rates *= -1000 # Same, reverse and convert
    isd['EPHEM_PTS'] = eph.flatten()
    isd['EPHEM_RATES'] = eph_rates.flatten()

    # Why should / should not the n_quaternions equal the number of ephemeris pts?
    n_quaternions = n_ephemeris
    isd['NUMBER_OF_QUATERNIONS'] = n_quaternions

    isd['DT_QUAT'] = isd['SCAN_DURATION'] / n_quaternions
    qua = np.empty((n_quaternions, 4))
    current_et = et
    for i in range(n_quaternions):
        # Find the rotation matrix
        camera2bodyfixed = spice.pxform('MRO_CTX', 'IAU_MARS', current_et)
        q = spice.m2q(camera2bodyfixed)
        qua[i][:3] = q[1:]
        qua[i][-1] = q[0]
        current_et += isd['DT_QUAT']
    isd['QUATERNIONS'] = qua.flatten()


    # Now the 'optional' stuff
    isd['REFERENCE_HEIGHT'] = data.get('reference_height', 30)
    isd['MIN_VALID_HT'] = data.get('min_valid_height' ,-8000)
    isd['MAX_VALID_HT'] = data.get('max_valid_height', 8000)
    isd['IMAGE_ID'] = data.get('image_id', 'UNKNOWN')
    isd['SENSOR_ID'] = data.get('sensor_id', 'USGS_LINE_SCANNER')
    isd['PLATFORM_ID'] = data.get('platform_id', 'UNKNOWN')
    isd['TRAJ_ID'] = data.get('traj_id', 'UNKNOWN')
    isd['COLL_ID'] = data.get('coll_id', 'UNKNOWN')
    isd['REF_DATE_TIME'] = data.get('ref_date_time', 'UNKNOWN')

    spice.unload(obs_kernels)

    return json.dumps(isd, cls=NumpyEncoder)
