import os
import json
import glob
import traceback
import logging
import pydicom
import errno
import time

import requests

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.operators.HelperOpensearch import HelperOpensearch
from kaapana.blueprints.kaapana_global_variables import SERVICES_NAMESPACE


class LocalMetaInstallOperator(KaapanaPythonBaseOperator):
    """ """

    def load_saved_obj(self, export_ndjson_path):
        files = {
            "file": open(export_ndjson_path, "rb"),
        }
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/saved_objects/_import?overwrite=true",
                headers={"osd-xsrf": "true"},
                files=files,
            )

            if response.status_code == 200:
                print("# Successfully import new os-dashboard objects-")
                print(f"# {export_ndjson_path}: OK!")
                print("#")

            elif response.text == "OpenSearch Dashboards server is not ready yet":
                print("#")
                print("# -> OpenSearch Dashboards server is not ready yet")
                print("# waiting ...")
                self.tries += 1
                time.sleep(10)
                print("# restart import os-dashboard objects ...")
                self.load_saved_obj()
                return

            else:
                print("#")
                print(f"# Could not import dashboard: {export_ndjson_path}")
                print(response.status_code)
                print(response.text)
                print("#")
                exit(1)
        except Exception as e:
            logging.error(traceback.format_exc())
            print("#")
            print(f"# Could not import dashboard: {export_ndjson_path} -> Exception")
            print("#")
            self.tries += 1
            print("# waiting ...")
            time.sleep(10)
            print("# restart import os-dashboard objects ...")
            self.load_saved_obj()

    def load_index_config(self, index_json_path):

        with open(index_json_path, "r") as file:
            index_dict = json.load(file)

        index_name = self.index
        # check if name is in the first key-level
        if index_dict.get(self.index):
            index_dict = index_dict[self.index]

        # remove invalid metadata for os-index-config
        index_body = index_dict
        if index_body.get("settings"):
            index_settings = index_body["settings"]["index"]
            index_settings.pop("creation_date",None)
            index_settings.pop("version",None)
            index_settings.pop("uuid",None)
            index_settings.pop("provided_name",None)
        print(index_body.get("settings"))
        # print("# INDEX-BODY:")
        # print(json.dumps(index_body, indent=4))
        # print("#")
        try:
            response = HelperOpensearch.os_client.indices.create(
                index_name, body=index_body
            )
            print("#")
            print("# Response:")
            print(response)
        except Exception as e:
            if str(e.error) == "resource_already_exists_exception":
                print("#")
                print("# Index already exists ... Delete and Recreate")
                self.delete_index()
                self.load_index_config(index_json_path)
                print("#")
            else:
                print("# ")
                print("# Unknown issue while creating the META index ...")
                print("# Error:")
                print(str(e))
                print("#")
                exit(1)

        print("#")
        print("# Success! ")
        print("#")

    def delete_index(self):
        print("# Delete old meta index...")
        response = HelperOpensearch.os_client.indices.delete(index=self.index)
        print(response)
        print("# Done deleting old meta index")

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

        for root, dirs, files in os.walk(input_dir):
            for file in files:

                if file.endswith(".json"):
                    print("Found new index config in input dir!")
                    self.load_index_config(os.path.join(root, file))

                if file.endswith(".ndjson"):
                    print("Found new obj-data in input dir!")
                    self.load_saved_obj(os.path.join(root, file))

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

        super().__init__(
            dag=dag,
            name="install-os-dashboard",
            python_callable=self.start,
            ram_mem_mb=10,
            **kwargs,
        )
