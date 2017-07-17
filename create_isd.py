from dateutil import parser
import spiceypy as spice

from utils import distort_focal_length


def isd_from_json(data, meta):
    # The instrument name does not match the naming convention used by spice, so we need another lookup
    instrument_name = {'MDIS-NAC':'MSGR_MDIS_NAC',
                   'MERCURY DUAL IMAGING SYSTEM NARROW ANGLE CAMERA':'MSGR_MDIS_NAC',
                   'MERCURY DUAL IMAGING SYSTEM WIDE ANGLE CAMERA':'MSGR_MDIS_WAC'}

    # This is the return dict
    isd = {}

    # Meta kernels are keyed by body, spacecraft, and year - grab from the data
    spacecraft_name = data['spacecraft_id']
    target_name = data['target_name']
    time = parser.parse(data['capture_date'])
    year = str(time.year)


    # Load the meta kernel
    obs_kernels = meta[target_name.lower()][spacecraft_name.lower()]
    spice.furnsh(obs_kernels[year][0])

    # Spice likes ids over names, so grab the ids from the names
    instrument_name = instrument_name[data['instrument']]
    spacecraft_id = spice.bods2c(spacecraft_name)
    ikid = spice.bods2c(instrument_name) * -1

    # Load the instrument and target metadata into the ISD
    isd['instrument_id'] = instrument_name
    isd['target_name'] = target_name
    isd['spacecraft_name'] = spacecraft_name

    # Prepend IAU to all instances of the body name
    reference_frame = 'IAU_{}'.format(target_name)

    # Load information from the IK kernel
    isd['focal_length_epsilon'] = spice.gdpool('INS-{}_FL_UNCERTAINTY'.format(ikid), 0, 1)
    isd['nlines'] = spice.gipool('INS-{}_PIXEL_LINES'.format(ikid), 0, 1)
    isd['nsamples'] = spice.gipool('INS-{}_PIXEL_SAMPLES'.format(ikid), 0, 1)
    isd['original_half_lines'] = isd['nlines'] / 2.0
    isd['original_half_samples'] = isd['nsamples'] / 2.0
    isd['pixel_pitch'] = spice.gdpool('INS-{}_PIXEL_PITCH'.format(ikid), 0, 1)
    isd['ccd_center'] = spice.gdpool('INS-{}_CCD_CENTER'.format(ikid), 0, 2)
    isd['ifov'] = spice.gdpool('INS-{}_IFOV'.format(ikid), 0, 1)
    isd['boresight'] = spice.gdpool('INS-{}_BORESIGHT'.format(ikid), 0, 3)
    isd['transx'] = spice.gdpool('INS-{}_TRANSX'.format(ikid), 0, 3)
    isd['transy'] = spice.gdpool('INS-{}_TRANSY'.format(ikid), 0, 3)
    isd['itrans_sample'] = spice.gdpool('INS-{}_ITRANSS'.format(ikid), 0, 3)
    isd['itrans_line'] = spice.gdpool('INS-{}_ITRANSL'.format(ikid), 0, 3)
    isd['odt_x'] = spice.gdpool('INS-{}_OD_T_X'.format(ikid), 0, 10)
    isd['odt_y'] = spice.gdpool('INS-{}_OD_T_Y'.format(ikid), 0, 10)
    isd['starting_detector_sample'] = spice.gdpool('INS-{}_FPUBIN_START_SAMPLE'.format(ikid), 0, 1)
    isd['starting_detector_line'] = spice.gdpool('INS-{}_FPUBIN_START_LINE'.format(ikid), 0, 1)



    # Get the radii from SPICE
    rad = spice.bodvrd(isd['target_name'], 'RADII', 3)
    radii = rad[1]
    isd['semi_major_axis'] = rad[1][0]
    isd['semi_minor_axis'] = rad[1][1]

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

    return isd
