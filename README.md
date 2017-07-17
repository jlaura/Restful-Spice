# RESTful Spice a.k.a. Pfeffernusse


This project uses the NAIF supplied spice data and exposes it as a RESTful service.  This is a **prototype** proof of concept with no documentation.  The module depends on:

- spiceypy
- flask
- numpy

Optionally, the `pvl` library is being used to read PVL labels in the example ipython notebooks.

- pvl

## Necessary Changes

*In the future we will do a config file that does this stuff.*

If you would like to test this locally (we support MDIS-NAC/WAC) with no structural changes to the kernel data structures.  Simply change:

- `kernel_manager.py` - PATH to the `spice_root`

and ensure that the NAIF messenger data has been downloaded locally.


If you would like to try this with a different mission:

- `kernel_manager.py` - also update the `meta_kernels` dict with the necessary body and instrument keys
- `app.py` - update the `data['available_missions']` dict,
- download the necessary spice kernels locally

## Running the App

>>> `python app.py`

then in a browser navigate to `localhost:5000`.  The app is running in debug mode by default (can be changed at the end of `app.py`).
