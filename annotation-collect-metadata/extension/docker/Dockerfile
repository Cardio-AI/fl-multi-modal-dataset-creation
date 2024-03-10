FROM local-only/base-installer:latest

LABEL IMAGE="dag-annotation-collect-metadata"
LABEL VERSION="0.1.0"
LABEL CI_IGNORE="False"

COPY files/annotation_collect_metatdata_dags/* /kaapana/tmp/dags/
COPY files/annotation_collect_metadata /kaapana/tmp/dags/annotation_collect_metadata

RUN python -m pip install -c https://raw.githubusercontent.com/kaapana/kaapana/0.2.1/build-scripts/constraints-0.2.1.txt --no-cache-dir -r /kaapana/app/requirements.txt

# Overwrite the dag-installer script 
COPY files/install.py /kaapana/app/install.py
CMD ["python3","-u","/kaapana/app/install.py"]
