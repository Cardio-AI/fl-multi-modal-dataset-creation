# Multi-Modal Dataset Creation

This repository contains code for additional SR-template structures extending the [highdicom](https://github.com/ImagingDataCommons/highdicom) Python library. The following templates have been added to describe annotations for ECG reports (TID 3700):

- [TID 2000 (Basic Diagnostic Imaging Report)](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_A.html#sect_TID_2000)
- [TID 3700 (ECG Report)](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_ECGReportTemplates.html#table_TID_3700)
- [TID 3802 (Cardiovascular Patient History)](https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_TID_3802.html#table_TID_3802)

Additionally, a [Kaapana](https://github.com/kaapana/kaapana) extension has been developed to enable querying of annotation metadata(segmentation or structure reports) within their respective report modalities, such as images (CT, MR, CR...) or waveforms (ECG). This allows cohorts to be selected multimodally and with greater specificity to additional reports. To install the extension, refer to the instructions [here](https://github.com/Cardio-AI/fl-multi-modal-dataset-creation/blob/main/annotation-collect-metadata/README.md).

For more detailed description we refer to our associated [paper](https://doi.org/10.1007/978-3-658-44037-4_39).

## Abstract

The unification of electronic health records promises interoperability of medical data. Divergent data storage options, inconsistent naming schemes,
varied annotation procedures, and disparities in label quality, among other factors, pose significant challenges to the integration of expansive datasets especially
across instiutions. This is particularly evident in the emerging multi-modal learning paradigms where dataset harmonization is of paramount importance. Leveraging the DICOM standard, we designed a data integration and filter tool that streamlines the creation of multi-modal datasets. This ensures that datasets from various
locations consistently maintain a uniform structure. We enable the concurrent filtering of DICOM data (i.e. images and waveforms) and corresponding annotations
(i.e. segmentations and structured reports) in a graphical user interface. The graphical interface as well as example structured report templates is openly available at
https://github.com/Cardio-AI/fl-multi-modal-dataset-creation.

## License

### high-dicom SR templates

The high dicom-SR templates are [MIT licensed](./LICENSE).

### annotation-collect-metadata

The annotation-collect-metadata can redistribute and/or modify under the terms of the [GNU Affero General Public License](./annotation-collect-metadata/LICENSE).
For more information see [annotation-collect-metadata](./annotation-collect-metadata/README.md)

## Citation

```BibTeX
@InProceedings{10.1007/978-3-658-44037-4_39,
author="T{\"o}lle, Malte and Burger, Lukas and Kelm, Halvar and Engelhardt, Sandy",
editor="Maier, Andreas and Deserno, Thomas M. and Handels, Heinz and Maier-Hein, Klaus and Palm, Christoph and Tolxdorff, Thomas",
title="Towards Unified Multi-modal Dataset Creation for Deep Learning Utilizing Structured Reports",
booktitle="Bildverarbeitung f{\"u}r die Medizin 2024",
year="2024",
publisher="Springer Fachmedien Wiesbaden",
address="Wiesbaden",
pages="130--135",
isbn="978-3-658-44037-4"
}
```
