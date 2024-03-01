from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.utils.dates import days_ago
from datetime import timedelta
from airflow.models import DAG
from kaapana.operators.LocalGetInputDataOperator import LocalGetInputDataOperator
from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator

from annotation_collect_metadata.LocalAnnotationDcm2JsonOperator import LocalAnnotationDcm2JsonOperator
from annotation_collect_metadata.LocalAnnotationJson2MetaOperator import LocalAnnotationJson2MetaOperator

log = LoggingMixin().log

args = {
    "ui_visible": False,
    "owner": "system",
    "start_date": days_ago(0),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

dag = DAG(
    dag_id="service-extract-annotation-metadata",
    default_args=args,
    concurrency=50,
    max_active_runs=20,
    schedule_interval=None,
    tags=["service"],
)

get_input = LocalGetInputDataOperator(dag=dag, operator_out_dir="get-input-data")
extract_metadata = LocalAnnotationDcm2JsonOperator(dag=dag, input_operator=get_input)
push_json = LocalAnnotationJson2MetaOperator(
    dag=dag, input_operator=get_input, json_operator=extract_metadata
)

clean = LocalWorkflowCleanerOperator(dag=dag, clean_workflow_dir=True)

get_input >> extract_metadata >> push_json >> clean
