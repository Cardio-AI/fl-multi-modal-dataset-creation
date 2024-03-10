import os
import json
from typing import List
from pathlib import Path

from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.operators.HelperCaching import cache_operator_output
from annotation_collect_metadata.sr_meta import LocalSR2Meta


class LocalAnnotationDcm2JsonOperator(KaapanaPythonBaseOperator):
    """
    Operator to convert DICOM files to JSON.
    The operator uses the dcmtk tool dcm2json https://support.dcmtk.org/docs/dcm2json.html
    Additionally some keywords and values are transformed to increase the usability to find/search key-values.

    **Inputs:**

    * exit_on_error: exit with error, when some key/values are missing or mismatching.
    * delete_pixel_data: uses dcmtk's dcmodify to remove some specific to be known private tags
    * bulk: process all files of a series or only the first one (default)

    **Outputs:**

    * json file: output json file. DICOM tags are converted to a json file.
    """

    MODALITY_TAG = "00080060 Modality_keyword"
    IMAGE_TYPE_TAG = "00080008 ImageType_keyword"    

    @cache_operator_output
    def start(self, ds, **kwargs):
        print("Starting module annotationDcm2json...")
        print(kwargs)

        run_dir: Path = Path(self.airflow_workflow_dir, kwargs["dag_run"].run_id)
        batch_folder: List[Path] = list((run_dir / self.batch_name).glob("*"))

        with open(self.dict_path, encoding="utf-8") as dict_data:
            self.dictionary = json.load(dict_data)

        for batch_element_dir in batch_folder:
            dcm_files: List[Path] = sorted(
                list((batch_element_dir / self.operator_in_dir).rglob("*.dcm"))
            )

            if len(dcm_files) == 0:
                print("No dicom file found!")
                raise ValueError("ERROR")

            print("length", len(dcm_files))
            for dcm_file_path in dcm_files:
                print(f"Extracting annotation metadata: {dcm_file_path}")

                target_dir: Path = batch_element_dir / self.operator_out_dir
                target_dir.mkdir(exist_ok=True)

                json_file_path = target_dir / f"{batch_element_dir.name}.json"

                # extract metadata from annotations dcm files
                json_dict = LocalSR2Meta.extracted_annotation_meta(dcm_file_path)

                if len(json_dict) > 0:

                    # NOTE SEG, RSTRUCT and SRs are saved as child objects
                    with open(json_file_path, "w", encoding="utf-8") as jsonData:
                        json.dump(
                            json_dict, jsonData, indent=4, sort_keys=True, ensure_ascii=True
                        )

                # shutil.rmtree(self.temp_dir)
                if self.bulk == False:
                    break

    def __init__(
        self, dag, exit_on_error=False, bulk=False, **kwargs
    ):
        """
        :param exit_on_error: 'True' or 'False' (default). Exit with error, when some key/values are missing or mismatching.
        :param bulk: 'True' or 'False' (default). Process all files of a series or only the first one.
        """

        self.dcmodify_path = "annotation-dcmodify"
        self.dcm2json_path = "annotation-dcm2json"
        self.bulk = bulk
        self.exit_on_error = exit_on_error

        os.environ["PYTHONIOENCODING"] = "utf-8"
        if "DCMDICTPATH" in os.environ and "DICT_PATH" in os.environ:
            # DCMDICTPATH is used by dcmtk / dcm2json
            self.dict_path = os.getenv("DICT_PATH")
        else:
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("DCMDICTPATH or DICT_PATH ENV NOT FOUND!")
            print("dcmdictpath: {}".format(os.getenv("DCMDICTPATH")))
            print("dict_path: {}".format(os.getenv("DICT_PATH")))
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            raise ValueError("ERROR")

        super().__init__(
            dag=dag,
            name="annotation-dcm2json",
            python_callable=self.start,
            ram_mem_mb=10,
            **kwargs,
        )