ARG BUILD_FROM
FROM $BUILD_FROM

COPY requirements.txt /
RUN pip install -r requirements.txt

# Copy data for add-on
COPY wb_to_ha/ /wb_to_ha
COPY wb-to-ha-discovery.py /
COPY wb-to-ha-yaml.py /
COPY frontend/ /frontend
