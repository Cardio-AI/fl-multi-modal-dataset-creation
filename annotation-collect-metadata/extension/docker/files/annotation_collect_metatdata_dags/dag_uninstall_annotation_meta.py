from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.models import DAG
from kaapana.operators.LocalMinioOperator import LocalMinioOperator
from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator
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
    dag_id="uninstall-annotation-collect-meta",
    default_args=args,
    schedule_interval=None,
    concurrency=1,
    max_active_runs=1,
    tags=["extension"],
)


pull_index_from_minio = LocalMinioOperator(
    dag=dag,
    bucket_name="backup-meta-index",
    action_operator_dirs=["back_up_files"],
    operator_out_dir="back_up_files",
    file_white_tuples=(".json", ".ndjson"),
    zip_files=False,
)

install_old_meta = LocalMetaInstallOperator(
    dag=dag, input_operator=pull_index_from_minio
)

remove_index_from_minio = LocalMinioOperator(
    dag=dag,
    action='remove',
    bucket_name="backup-meta-index",
    action_operator_dirs=["back_up_files"],
)
# TODO remove annotation visualizations and dashboards
clean = LocalWorkflowCleanerOperator(dag=dag, clean_workflow_dir=True)

pull_index_from_minio >> install_old_meta >> remove_index_from_minio >> clean
