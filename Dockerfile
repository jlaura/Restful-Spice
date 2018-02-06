FROM continuumio/miniconda3

# Creating the working directory
WORKDIR /app

# Add the current directory as the working directory
ADD . /app

# Internal SSL issues
RUN conda config --set ssl_verify false 
# Install the necessary dependencies
RUN conda env create --file environment.yml
RUN /bin/bash -c "source activate pfeffernusse"

# Expose the flask development port
EXPOSE 5000

CMD ["/opt/conda/envs/pfeffernusse/bin/python", "app.py"]


