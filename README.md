# RESTful Spice a.k.a. Pfeffernusse


This project uses the NAIF supplied spice data and exposes it as a RESTful service.  This is a **prototype** proof of concept with no documentation.  As an *alpha* product, Pfeffernusse is not ready for production.  The functionality of pfeffernusse is also currently conflated some with the SpiceRack project.  In coming releases we will separate these microservices with spicerack supporting management of kernels, distributed synchronization, and a light RESTful API to report kernel availability.  This project will then be able to focus on exploitation of the kernels and generation of higher order data packages, e.g., a Community Sensor Model compliant Image Support Data (ISD) blob.

## Dependencies
The module depends on:
- spiceypy
- flask
- sqlalchemy

- numpy

Optionally, to run the example ipython notebooks.

- pvl
- requests

## Running the App in Development Mode
>>> `python setup.py develop`  # To get the pfeffernusse module installed
>>> `python run.py`

then in a browser navigate to `localhost:5000`.  The app is running in debug mode by default (can be changed at the end of `run.py`).

## Running the App as a MicroService
This is how we intend Pfeffernusse to be deployed. Simply running the following will get Pfeffernusse up and running as a Docker container.

>>> `docker run -p <hostport>:5000 -v <host_spice_root>:/spice/data usgsastro/pfeffernusse`  

## Running the App with a different Spice Root
The app assumes that spice data is stored in `/data/spice`.  This is done intentionally as we intend the application to be run as a containerized microservice.  If you will to change the root directory:
1. Inside of `/bin/create_spice_db.py` change the `ROOT` to the desired root.
2. Remove `mk.db` and rerun `/bin/create_spice_db.py` to update the PATH info that is being stored in the database.
