from datetime import timedelta
import pydicom
from shutil import copyfile
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.models import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule

from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator
from kaapana.operators.LocalMinioOperator import LocalMinioOperator
from kaapana.blueprints.kaapana_global_variables import AIRFLOW_WORKFLOW_DIR
from annotation_collect_metadata.LocalMetaBackupOperator import LocalMetaBackupOperator
from annotation_collect_metadata.LocalMetaInstallOperator import (
    LocalMetaInstallOperator,
)


args = {
    "ui_visible": False,
    "owner": "system",
    "start_date": days_ago(0),
    "retries": 0,
    "retry_delay": timedelta(seconds=10),
}

dag = DAG(
    dag_id="install-annotation-collect-meta",
    default_args=args,
    schedule_interval=None,
    concurrency=1,
    max_active_runs=1,
    tags=["extension"],
)


def get_annotation_os_data(ds, **kwargs):
    import os

    print("Copy annotation os-dashboard object and index...")
    # TODO can be copied directly in data folder, when volume-claim in jobs/delete is added
    data_dir = (
        "/kaapana/mounted/workflows/dags/annotation_collect_metadata/os_dashboard_data"
    )
    run_dir = os.path.join(AIRFLOW_WORKFLOW_DIR, kwargs["dag_run"].run_id)
    target_dir = os.path.join(run_dir, "get-input-data")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for file in os.listdir(data_dir):
        abs_file_path = os.path.join(data_dir,file)
        print(f"Copy {abs_file_path}...")
        copyfile(abs_file_path, os.path.join(target_dir, file))


copy_annotation_data = PythonOperator(
    task_id="get-annotation-os-data",
    provide_context=True,
    pool="default_pool",
    executor_config={"cpu_millicores": 100, "ram_mem_mb": 50},
    python_callable=get_annotation_os_data,
    dag=dag,
)

backup_old_index = LocalMetaBackupOperator(
    dag=dag,
    operator_in_dir="get-input-data",
    operator_out_dir="back_up_files",
)

put_to_minio = LocalMinioOperator(
    dag=dag,
    name="backup-index2mino",
    zip_files=False,
    action="put",
    bucket_name="backup-meta-index",
    action_operators=[backup_old_index],
    file_white_tuples=(".json", ".ndjson"),
)

install_new_meta_index = LocalMetaInstallOperator(
    dag=dag, operator_in_dir="get-input-data"
)

# trigger annotation reindex
trigger_reindex_task = TriggerDagRunOperator(
    dag=dag,
    task_id="trigger-re-index-pacs",
    trigger_dag_id="service-re-index-dicom-data",
    trigger_rule=TriggerRule.ALL_SUCCESS,
)

clean = LocalWorkflowCleanerOperator(dag=dag, clean_workflow_dir=True)

copy_annotation_data >> backup_old_index >> put_to_minio >> clean >> trigger_reindex_task
copy_annotation_data >> backup_old_index >> install_new_meta_index >> clean >> trigger_reindex_task
