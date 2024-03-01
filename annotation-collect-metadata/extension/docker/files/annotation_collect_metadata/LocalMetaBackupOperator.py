import os
import json
import glob
import traceback
import logging
import pydicom
import errno
import time
from datetime import datetime

import requests

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.operators.HelperOpensearch import HelperOpensearch
from kaapana.blueprints.kaapana_global_variables import SERVICES_NAMESPACE


class LocalMetaBackupOperator(KaapanaPythonBaseOperator):
    """ """

    def save_saved_obj(self):

        if self.tries > 5:
            print("# ")
            print(f"# Too many tries: {self.tries} -> abort.")
            return None

        try:
            response = requests.post(
                f"{self.dashboard_url}/api/saved_objects/_export",
                headers={"osd-xsrf": "true", "Content-Type": "application/json"},
                json={
                    "type": [
                        "visualization",
                        "config",
                        "dashboard",
                        "url",
                        "index-pattern",
                        "query",
                        "visualization-visbuilder",
                        "map",
                        "search",
                    ],
                    "includeReferencesDeep": True,
                },
            )
            if response.status_code == 200:
                # Write exported data to file
                print("Download objects successfully.")
                obj_out_path = os.path.join(self.out_dir, f"saved_objects_{self.time_string}.ndjson")
                with open(obj_out_path, "wb") as f:
                    f.write(response.content)
                print(f"Wrote objects to {obj_out_path}.")
            else:
                logging.error(traceback.format_exc())
                print("#")
                print(
                    f"# Could not export dashboard: -> Exception {response.status_code}"
                )
                print("#")
                self.tries += 1
                print("# waiting ...")
                time.sleep(10)
                print("# restart export_dashboards() ...")
                self.save_saved_obj()
                print("Failed to export saved objects.")
        except:
            logging.error(traceback.format_exc())
            print("#")
            print(f"# Could not export dashboard: -> Exception")
            print("#")
            self.tries += 1
            print("# waiting ...")
            time.sleep(10)
            print("# restart export_dashboards() ...")
            self.save_saved_obj()
            print("Failed to export saved objects.")

    def save_index_config(self):
        try:
            index_config = HelperOpensearch.os_client.indices.get(index=self.index)
            index_config = index_config[self.index] # get configs from index
            index_out_path = os.path.join(self.out_dir, f"{self.index}_config_{self.time_string}.json")
            with open(index_out_path, "w") as f:
               json.dump(index_config,f)
            print(f"Wrote index configuration to {index_out_path}.")
        except Exception as e:
            print(f"Error saving index configuration: {str(e)}")

    def start(self, ds, **kwargs):
        # TODO fix folder structure
        # run_dir = os.path.join(self.airflow_workflow_dir, kwargs["dag_run"].run_id)
        # batch_folder = [
        #     f for f in glob.glob(os.path.join(run_dir, self.batch_name, "*"))
        # ]
        self.run_id = kwargs["dag_run"].run_id
        print(("RUN_ID: %s" % self.run_id))

        input_dir = os.path.join(
            self.airflow_workflow_dir, self.run_id, self.operator_in_dir
        )
        self.out_dir = os.path.join(
            self.airflow_workflow_dir, self.run_id, self.operator_out_dir
        )

        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)

        for root, dirs, files in os.walk(input_dir):
            for file in files:
                # Get the current date and time
                current_time = datetime.now()
                self.time_string = current_time.strftime("%Y%m%d_%H%M%S")

                if file.endswith(".json"):
                    print("Found index-config file, backup old index!")
                    self.save_index_config()

                if file.endswith(".ndjson"):
                    print("Found saved-objects file, backup old object!")
                    self.save_saved_obj()

    def __init__(
        self,
        dag,
        index_name="meta-index",
        tires=5,
        **kwargs,
    ):

        self.index = index_name
        self.tries = tires
        self.dashboard_url = (
            f"http://os-dashboards-service.{SERVICES_NAMESPACE}.svc:5601/meta"
        )
        self.out_dir = None
        self.time_string = None

        super().__init__(
            dag=dag,
            name="backup-meta-dashboard",
            python_callable=self.start,
            ram_mem_mb=10,
            **kwargs,
        )
