from typing import Sequence
import pydicom
from datetime import datetime
from dateutil import parser
import pytz
from annotation_collect_metadata.sr_reader import SR_Reader


class LocalSR2Meta:

    # used same time format as in extract metadata
    format_time = "%H:%M:%S.%f"
    format_date = "%Y-%m-%d"
    format_date_time = "%Y-%m-%d %H:%M:%S.%f"

    @staticmethod
    def extracted_annotation_meta(dcm_file_path: str):
        dcm_data = pydicom.dcmread(dcm_file_path, stop_before_pixels=True)
        dcm_data.decode()

        return LocalSR2Meta.extract_meta(dcm_data)

    @staticmethod
    def extract_meta(dcm_data: pydicom.Dataset, references_instance_UIDs: list = None):
        print("# Extract annotation DCM meta...")

        if dcm_data is None:
            print("Empty report, could not update")
            exit(1)

        # check for reference series in report
        references_ids = LocalSR2Meta.extract_reference_ids(dcm_data)
        if len(references_ids) > 0:
            print("Ref-IDs found:", references_ids)
        elif references_instance_UIDs is not None:
            references_ids = references_instance_UIDs
        else:
            print("# No ref-IDs found! - exit")
            exit(1)

        # refactor annotation data, for better filter options
        report_json = LocalSR2Meta.get_meta(dcm_data)
        report_json["99999999 ReferencedSeriesIDs_keyword"] = references_ids

        return report_json

    @staticmethod
    def get_meta(dcm_data: pydicom.Dataset):
        modality = dcm_data.Modality
        print("Starting extract content:", dcm_data.SeriesInstanceUID)
        meta_data = {}

        # add general annotation meta-data
        meta_data["0020000E SeriesInstanceUID_keyword"] = dcm_data.get(
            "SeriesInstanceUID"
        )
        meta_data["99999999 ContentDate_date"] = dcm_data.get("ContentDate")
        meta_data["99999999 ContentTime_time"] = dcm_data.get("ContentTime")
        meta_data["99999999 Modality_keyword"] = dcm_data.get("Modality")

        # add specific content meta-data
        content_meta = {}
        if modality == "SR":
            content_meta = LocalSR2Meta.get_sr_meta(dcm_data)
        elif modality == "SEG":
            content_meta = LocalSR2Meta.get_seg_meta(dcm_data)
        elif modality == "RTSTRUC":
            content_meta = LocalSR2Meta.get_rstruc_meta(dcm_data)
        else:
            print("Annotation modality ", modality, "is not supported.")
        meta_data.update(content_meta)

        # format time according to the meta-index in opensearch
        meta_data = LocalSR2Meta.format_time_fields(meta_data)

        return meta_data

    @staticmethod
    def get_sr_meta(dcm_data: pydicom.Dataset) -> dict:
        print("Start SR-report meta extraction subprocess")
        meta_data = {}
        try:
            # get general fields from SR reports
            # flags
            meta_data["99999999 CompletionFlag_keyword"] = dcm_data.get(
                "CompletionFlag"
            )
            meta_data["99999999 VerificationFlag_keyword"] = dcm_data.get(
                "VerificationFlag"
            )
            meta_data["99999999 PreliminaryFlag_keyword"] = dcm_data.get(
                "PreliminaryFlag"
            )

            # get SR-report specific types from templates
            template_data = SR_Reader.extract_template_data(dcm_data)
            meta_data.update(template_data)

        except ValueError:
            print("Not all values are supported!")

        return meta_data

    @staticmethod
    def get_seg_meta(dcm_data: pydicom.Dataset) -> dict:
        print("Start segmentation meta extraction subprocess")
        meta_data = {}
        try:
            meta_data["99999999 ContentCode_keyword"] = (
                "113076"  # Meaning:'Segmentation', Schema:'dcm'
            )
            meta_data["99999999 ContentLabel_keyword"] = dcm_data.get("ContentLabel")
            meta_data["99999999 ContentDescription_keyword"] = dcm_data.get(
                "ContentDescription"
            )
            meta_data["99999999 ContentKey_keyword"] = "Segmentation"

            anatomical_regions = list()
            anatomical_struct = list()

            segment_seq = dcm_data.get("SegmentSequence")
            if segment_seq:
                for segmentation in segment_seq:
                    if segmentation.get("AnatomicRegionSequence"):
                        # is a set/list of anatomic regions
                        anatomical_seq = segmentation.AnatomicRegionSequence[0]
                        anatomical_regions.append(anatomical_seq.CodeMeaning)

                    if segmentation.get("SegmentedPropertyTypeCodeSequence"):
                        # is a set/list of anatomic regions
                        property_seq = segmentation.SegmentedPropertyTypeCodeSequence[0]
                        anatomical_struct.append(property_seq.CodeMeaning)

            meta_data["99999999 AnatomicRegionSequence_keyword"] = anatomical_regions
            meta_data["99999999 AnatomicalStructure_keyword"] = anatomical_struct

        except:
            raise ValueError("Not a SEG file.")

        return meta_data

    @staticmethod
    def get_rstruc_meta(dcm_data: pydicom.Dataset) -> dict:
        try:
            # TODO Implement the logic for RTSTRUC metadata extraction here
            pass
        except:
            raise NotImplementedError("RTSTRUC files are not supported, yet.")

    @staticmethod
    def get_ids_from_seq(referenced_series_sequence):
        references_ids = []
        if not isinstance(referenced_series_sequence, Sequence):
            referenced_series_sequence = [referenced_series_sequence]
            for reference_series in referenced_series_sequence:
                id = reference_series.get("SeriesInstanceUID")
                references_ids.append(id)

        return references_ids

    @staticmethod
    def extract_reference_ids(dcm_data: pydicom.Dataset):
        print("Extract reference series ids from report")
        references_ids = []

        # look for ReferencedSeriesSequence in nested Sequences
        if dcm_data.get("PertinentOtherEvidenceSequence"):
            dcm_data = pydicom.Dataset(
                dcm_data.get("PertinentOtherEvidenceSequence")[0]
            )
        elif dcm_data.get("CurrentRequestedProcedureEvidenceSequence"):
            dcm_data = pydicom.Dataset(
                dcm_data.get("CurrentRequestedProcedureEvidenceSequence")[0]
            )

        # look ReferencedSeriesSequence in the root level
        if dcm_data.get("ReferencedSeriesSequence"):
            referenced_series_sequence = dcm_data.get("ReferencedSeriesSequence")[0]
            references_ids.extend(
                LocalSR2Meta.get_ids_from_seq(referenced_series_sequence)
            )

        references_ids = list(set(references_ids))

        return references_ids

# Helper function to change the time-format according to the DCM2JSON workflow of KAAPANA

    @staticmethod
    def format_time_fields(data: dict):
        # format the time files according to the opensearch-index definition
        for key in data.keys():
            if key.split("_")[-1] == "time":
                data[key] = format_time(data[key])
            elif key.split("_")[-1] == "date":
                data[key] = format_date(data[key])
            elif key.split("_")[-1] == "date_time":
                data[key] = format_date_time(data[key])

        return data


def format_date(date_str):
    date_formatted = parser.parse(date_str).strftime(LocalSR2Meta.format_date)

    return date_formatted


def format_time(time_str):
    hour = 0
    minute = 0
    sec = 0
    fsec = 0
    if "." in time_str:
        time_str = time_str.split(".")
        if time_str[1] != "":
            # FIXME: unsafe with leading zeros (160504.0123, but ok if exactly 6 digits)
            fsec = int(time_str[1])
        time_str = time_str[0]
    if len(time_str) == 6:
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        sec = int(time_str[4:6])
    elif len(time_str) == 4:
        minute = int(time_str[:2])
        sec = int(time_str[2:4])

    elif len(time_str) == 2:
        sec = int(time_str)

    else:
        print(
            "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ could not convert time!"
        )
        print("time_str: {}".format(time_str))

    # HH:mm:ss.SSSSS
    time_string = "%02i:%02i:%02i.%06i" % (hour, minute, sec, fsec)
    time_formatted = parser.parse(time_string).strftime(LocalSR2Meta.format_time)

    return time_formatted


def format_date_time(date_time_str: str):
    date_time_formatted = parser.parse(date_time_str).strftime(
        LocalSR2Meta.format_date_time
    )
    date_time_formatted = LocalSR2Meta.convert_time_to_utc(
        date_time_formatted, LocalSR2Meta.format_date_time
    )

    return date_time_formatted


# FIXME: hard-coded timezone used for DICOM tag values -> See DCM2JSON operator
def convert_time_to_utc(time_berlin, date_format):
    local = pytz.timezone("Europe/Berlin")
    naive = datetime.strptime(time_berlin, date_format)
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)

    return utc_dt.strftime(date_format)
