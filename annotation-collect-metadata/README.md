# Annotation meta data

The 'annotation metadata' extension modifies the Kaapana workflow to extract metadata for the OpenSearch service. It adjusts the indexing of annotation files (currently DICOM files with the modalities SEG and SR) to store them as nested objects within their referenced series files (DICOM files with image modalities such as MR, ECG, CT, etc.). Moreover, it categorizes the annotation files to enhance their visualization. These alterations enable users to execute queries on the dashboard using both the series data elements and their associated annotation files, facilitating the selection of their cohort.


## Installation workflow

The workflow can be loaded as [Kaapana extension](https://kaapana.readthedocs.io/en/stable/development_guide/workflow_dev_guide.html#step-4-add-extension-to-the-platform). However, it involves a manual installation process within a DAG workflow and overrides existing workflows of the default Kaapana platform. These files are backed up during the process and recovered if uninstalled. Also, during the installation workflow, the process backs up the OpenSearch meta-index (configuration-file) and the existing objects(dashboard,visualizations...) in a MinIO bucket. Furthermore, the index and objects are then **overwritten** with the new annotation objects and meta-index configuration.

To configure which information is loaded from the SR DICOM files, the definition can be updated in the [annotation_meta_templates.py](./extension/docker/files/annotation_collect_metadata/annotation_meta_templates.py) file. It is defined with the template ID (TID) and loads the necessary information based on it, meaning that only SR documents with defined TIDs in this file are supported.
The content of the SR document is then searched hierarchically with the definition provided in the `struct` field and sorts the information into categories based on their content value type:

- Qualitative: "CODE",
- Quantitative: "NUM",
- Point: "SCOORD", "SCOORD3D",
- UnstructuredText: "TEXT"
  
Additionally, constraints such as specific code values can be included at each level in the `constraints` field to select from multiple values at the same level. Otherwise, the first found type match will be added to the OS-index.

The extension was developed and tested with [KAAPANA v0.2.6](https://github.com/kaapana/kaapana/releases/tag/0.2.6).

> [!CAUTION]
> At the current version the meta-index and the opensearch-objects(dashboard, graphs,...) are overwritten with a empty/new one and a re-index pacs workflow is triggered afterwards. Please backup important data from the meta-index manually, if you plan to install this extension.
> 
> In the current version following functionality from kaapana are changed:
> - Segmentation thumbnails are disabled in the data view.
> - Only dicom files with the modality `CT,MR,DX,MG,CR,ECG,XA,US,PT` are saved the same way as in kaapana in the OS-index. Other modalities are only save in the PACS.
> - Dicom files with the modality `SR` and `SEG` are saved in the OS-Index as nested object, if the reference ID exits. Else there are only save in the PACS.
> - Re-index dicom data is iterating two times over all pacs-data and extract in the first iteration the meta data from the `CT,MR,DX,MG,CR,ECG,XA,US,PT` modalities and in the second iteration from the annotation information (`SR, SEG`)
> - The modality `RTSTRUCT` is not supported for annotation, yet.
