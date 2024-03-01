from datetime import timedelta
import pydicom
from shutil import copyfile
from airflow.operators.python import PythonOperator
from airflow.models import DAG,DagRun
from airflow.utils.dates import days_ago
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.sensors.external_task import BaseSensorOperator

from kaapana.blueprints.kaapana_utils import generate_run_id
from kaapana.blueprints.kaapana_global_variables import AIRFLOW_WORKFLOW_DIR, BATCH_NAME
from kaapana.operators.LocalDeleteFromMetaOperator import LocalDeleteFromMetaOperator
from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator
from airflow.utils.state import DagRunState

from typing import Union


class CheckDagRunningSensor(BaseSensorOperator):
    """
    Custom sensor that checks if any instance of a specific DAG is in defined mode.
    """
    
    def __init__(self, search_dag_id:str, search_mode:Union[DagRunState,None]=None,*args,**kwargs):
        self.search_dag_id = search_dag_id
        self.search_mode = search_mode
        super().__init__(*args,**kwargs)

    def poke(self, context):
        # Check if any instance of the DAG is in search_mode
        dag_runs = DagRun.find(dag_id=self.search_dag_id,state=self.search_mode)

        if dag_runs:
            # Some instances are still in search_mode, sensor should reschedule
            print(f"Poking for {self.search_dag_id} running instances. Found: {str(len(dag_runs))}")
            return False
        else:
            # No instances are in search_mode, sensor can proceed
            return True

args = {
    "ui_visible": False,
    "owner": "system",
    "start_date": days_ago(0),
    "retries": 0,
    "retry_delay": timedelta(seconds=10),
}

dag = DAG(
    dag_id="service-re-index-dicom-data",
    default_args=args,
    schedule_interval=None,
    concurrency=1,
    max_active_runs=1,
    tags=["service"],
)

clean_meta = LocalDeleteFromMetaOperator(
    dag=dag, operator_in_dir="get-input-data", delete_all_documents=True
)

def start_reindexing(ds, **kwargs):
    import os
    import glob
    from airflow.api.common.trigger_dag import trigger_dag as trigger
    import time

    pacs_data_dir = "/kaapana/mounted/pacsdata"
    dag_id = "service-extract-metadata"

    print("Start re-index")
    count_running_dags = lambda directory, dag_id: len([x for x in os.listdir(directory) if dag_id in x])
    MAX_NUM_CONCURRENCY = 200

    dcm_dirs = []
    file_list = glob.glob(pacs_data_dir + "/*/**/*", recursive=True)
    for fi in file_list:
        if os.path.isfile(fi):
            dcm_dirs.append(os.path.dirname(fi))
    dcm_dirs = list(set(dcm_dirs))

    print("Files found: {}".format(len(file_list)))
    print("Dcm dirs found: {}".format(len(dcm_dirs)))
    for dcm_dir in dcm_dirs:
        current_workflow_runs = count_running_dags(AIRFLOW_WORKFLOW_DIR, dag_id)
        dag_run_id = generate_run_id(dag_id)
        print("Run-id: {}".format(dag_run_id))

        dcm_file = os.path.join(dcm_dir, os.listdir(dcm_dir)[0])
        print("DIR: {}".format(dcm_dir))
        print("dcm-file: {}".format(dcm_file))
        incoming_dcm = pydicom.dcmread(dcm_file)
        seriesUID = incoming_dcm.SeriesInstanceUID
        modality = incoming_dcm.Modality

        while current_workflow_runs > MAX_NUM_CONCURRENCY:
            current_workflow_runs = count_running_dags(AIRFLOW_WORKFLOW_DIR, dag_id)
            time.sleep(10) # give some time to clean workflows

        if modality in ["CT,MR,DX,MG,CR,ECG,XA,US,PT"]:
            target_dir = os.path.join(
                AIRFLOW_WORKFLOW_DIR,
                dag_run_id,
                BATCH_NAME,
                "{}".format(seriesUID),
                "get-input-data",
            )
            print(target_dir)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            copyfile(
                dcm_file, os.path.join(target_dir, os.path.basename(dcm_file) + ".dcm")
            )

            trigger(dag_id=dag_id, run_id=dag_run_id, replace_microseconds=False)


reindex_pacs = PythonOperator(
    task_id="reindex-pacs",
    provide_context=True,
    pool="default_pool",
    executor_config={"cpu_millicores": 100, "ram_mem_mb": 50},
    python_callable=start_reindexing,
    dag=dag,
)
clean = LocalWorkflowCleanerOperator(dag=dag, clean_workflow_dir=True)

# task to wait to finish reindex the series metadata
wait_for_reindex = CheckDagRunningSensor(
    search_dag_id='service-extract-metadata',  # Specify the DAG ID to check
    search_mode=DagRunState.RUNNING,
    task_id='check_dag_running',
    mode='poke',
    poke_interval=300,  # Set the poke interval in seconds (5 minutes)
    timeout=24*60*60,  # Set a timeout of 1 day
    retries=1,  # Set the number of retries
    dag=dag,
)

# trigger annotation reindex
my_trigger_task = TriggerDagRunOperator(
    dag=dag,
    task_id="trigger-annotation-re-index",
    trigger_dag_id="service-re-index-annotation-data",
    trigger_rule=TriggerRule.ALL_SUCCESS,
)

clean_meta >>reindex_pacs >> clean >> wait_for_reindex >> my_trigger_task
