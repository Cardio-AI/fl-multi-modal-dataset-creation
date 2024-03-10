from datetime import timedelta
import pydicom
from shutil import copyfile
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.models import DAG
from kaapana.blueprints.kaapana_utils import generate_run_id
from kaapana.blueprints.kaapana_global_variables import AIRFLOW_WORKFLOW_DIR, BATCH_NAME
from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator


args = {
    "ui_visible": False,
    "owner": "system",
    "start_date": days_ago(0),
    "retries": 0,
    "retry_delay": timedelta(seconds=10),
}

dag = DAG(
    dag_id="service-re-index-annotation-data",
    default_args=args,
    schedule_interval=None,
    concurrency=1,
    max_active_runs=1,
    tags=["service"],
)

def start_meta_reindexing(ds, **kwargs):
    import os
    import glob
    from airflow.api.common.trigger_dag import trigger_dag as trigger

    pacs_data_dir = "/kaapana/mounted/pacsdata"
    dag_id = "service-extract-annotation-metadata"
    count_running_dags = lambda directory, dag_id: len([x for x in os.listdir(directory) if dag_id in x])
    MAX_NUM_CONCURRENCY = 200

    print("Start annotation re-index")

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

        if modality in ["SR","SEG"]:
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


meta_reindex_pacs = PythonOperator(
    task_id="meta-reindex-pacs",
    provide_context=True,
    pool="default_pool",
    executor_config={"cpu_millicores": 100, "ram_mem_mb": 50},
    python_callable=start_meta_reindexing,
    dag=dag,
)
clean = LocalWorkflowCleanerOperator(dag=dag, clean_workflow_dir=True)

meta_reindex_pacs >> clean
