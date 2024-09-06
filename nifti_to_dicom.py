
import time
from pathlib import Path
import shutil
import string
import numpy as np
import pyffx
import SimpleITK as sitk
import pydicom
from pydicom.uid import generate_uid
from highdicom.seg import (
    Segmentation, 
    SegmentDescription
)


def series_and_sop_instance_uid_from_slice(dcm_slice, series_number=1, seed=42):
    patient_id = dcm_slice.PatientID
    study_instance_uid = dcm_slice.StudyInstanceUID
    
    series_instance_uid = generate_uid(
        entropy_srcs=[
            study_instance_uid,
            # value.CodeMeaning,
            str(seed),
        ]
    )

    prefix = (
        ".".join(series_instance_uid.split(".")[:4]) + "."
    )  # ugly syntax for strap the prefix from the series uid and reuse it for slice identifier but w/e
    sop_instance_uid = generate_uid(
        prefix=prefix,
        entropy_srcs=[patient_id, study_instance_uid, series_instance_uid, str(series_number), str(seed)],
    )
    return series_instance_uid, sop_instance_uid

def pseudonymize_dcm(ds, pseudo_key):
    def _pseudo_string(x):
        alphabet = string.digits + string.ascii_letters + ' -^.'
        e = pyffx.String(
            pseudo_key.encode(),
            alphabet=alphabet,
            length=len(x)
        )
        return e.encrypt(x)
    ds.remove_private_tags()
    ds.PatientName = 'PLACE^HOLDER'
    ds.PatientID = _pseudo_string(ds.PatientID)
    ds.PatientBirthDate = '19300101'
    attrs = [
        'PatientAddress',
        'RequestingService',
        'ReferringPhysicianName',
        'InstitutionName',
        'InstitutionAddress',
        'StationName',
        'AcquisitionDateTime',
        'AcquisitionTime',
        'ContentTime'
    ]
    for attr in attrs:
        if hasattr(ds, attr):
            delattr(ds, attr)
    return ds


def write_slices(new_img, series_tag_values, i, out_fname, seed=42):
    image_slice = new_img[:, :, i]
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()
    writer.UseCompressionOn()  # Uses JPEG 2000 Lesless by default.

    patient_id = series_tag_values["0010|0020"]
    study_uid = series_tag_values["0020|000d"]
    series_uid = series_tag_values["0020|000e"]

    prefix = (
        ".".join(series_uid.split(".")[:4]) + "."
    )  # ugly syntax for strap the prefix from the series uid and reuse it for slice identifier but w/e
    slice_instance_uid = generate_uid(
        prefix=prefix,
        entropy_srcs=[patient_id, study_uid, series_uid, str(i), str(seed)],
    )

    series_tag_values["0008|0018"] = slice_instance_uid

    # set metadata shared by series
    for tag, value in series_tag_values.items():
        image_slice.SetMetaData(tag, value)

    # set slice specific metadata tags.
    image_slice.SetMetaData(
        "0008|0012", time.strftime("%Y%m%d")
    )  # Instance Creation Date
    image_slice.SetMetaData(
        "0008|0013", time.strftime("%H%M%S")
    )  # Instance Creation Time

    # (0020, 0032) image position patient determines the 3D spacing between slices.
    image_slice.SetMetaData(
        "0020|0032",
        "\\".join(map(str, new_img.TransformIndexToPhysicalPoint((0, 0, i)))),
    )  # Image Position (Patient)
    image_slice.SetMetaData("0020|0013", str(i))  # Instance Number

    # Write to the output directory and add the extension dcm, to force writing in DICOM format.
    writer.SetFileName(out_fname)
    writer.Execute(image_slice)


def img_to_dcm(
        fname, 
        modality,
        study_description,
        series_description,
        study_id,
        series_number,
        patient_id,
        patient_name,
        operator_name,
        manufacturer,
        manufacturer_model_name=None,
        patient_sex=None,
        patient_age=None,
        patient_weight=None,
        patient_size=None,
        patient_birth_date=None, # NEEDED FOR SEG
        tmp_dir='./tmp',
        seed=42
    ):
    img = sitk.ReadImage(fname)
    castFilter = sitk.CastImageFilter()
    castFilter.SetOutputPixelType(sitk.sitkInt16)
    imgFiltered = castFilter.Execute(img)

    study_instance_uid = generate_uid(
        entropy_srcs=[
            study_id,
            operator_name,
            str(seed),
        ]
    )

    frame_of_reference_uid = generate_uid(
        entropy_srcs=[
            study_id,
            operator_name,
            str(seed),
        ]
    )
    x_dim, y_dim, z_dim = img.GetSize()

    series_instance_uid = generate_uid(
        entropy_srcs=[
            study_instance_uid,
            series_description,
            str(seed),
        ]
    )

    series_tag_values = {
        "0008|0060": modality,
        "0008|1030": study_description,
        "0010|0020": patient_id,
        "0010|0010": patient_name,
        "0008|0070": manufacturer,
        "0020|0010": study_id,
        "0008|1070": operator_name,
        "0020|000d": study_instance_uid,
        "0020|0052": frame_of_reference_uid,
        "0020|000e": series_instance_uid,
        "0008|0031": time.strftime("%H%M%S"),
        "0008|0021": time.strftime("%Y%m%d"),
        "0020|0011": str(series_number)
    }
    if manufacturer_model_name is not None:
        series_tag_values["0008|1090"] = manufacturer_model_name
    if patient_sex is not None:
        series_tag_values['0010|0040'] = patient_sex
    if patient_age is not None:
        series_tag_values['0010|1010'] = patient_age
    if patient_weight is not None:
        series_tag_values['0010|1030'] = patient_weight
    if patient_size is not None:
        series_tag_values['0010|1020'] = patient_size
    if patient_birth_date is not None:
        series_tag_values['0010|0030'] = patient_birth_date

    tmp_created = False
    tmp_dir = Path(tmp_dir)
    if not tmp_dir.exists():
        tmp_dir.mkdir()
        tmp_created = True
    dcm_slices_fnames = []
    for j in range(z_dim):
        out_fname = Path(tmp_dir) / f'{series_number}_{j}.dcm'
        write_slices(imgFiltered, series_tag_values, j, str(out_fname), seed)
        dcm_slices_fnames.append(out_fname)
    dcm_slices = []
    for x in dcm_slices_fnames:
        dcm_slices.append(pydicom.dcmread(x))
        x.unlink()
    if tmp_created:
        shutil.rmtree(tmp_dir)
    return dcm_slices


def seg_to_dcm(
        fname,
        dcm_slices,
        series_number,
        content_description,
        content_creator_name,
        content_label,
        segment_descriptions,
        manufacturer,
        manufacturer_model_name,
        device_serial_number,
        software_versions,
        # fractional_type=SegmentationTypeValues.BINARY,
        segmentation_type='BINARY', # 'FRACTIONAL'
        seed=42
):
    seg = sitk.ReadImage(fname)
    seg_np = sitk.GetArrayFromImage(seg)

    if len(dcm_slices) > 1:
        if seg.GetSize()[2] != len(dcm_slices):
            raise ValueError
    
    patient_id = dcm_slices[0].PatientID
    study_instance_uid = dcm_slices[0].StudyInstanceUID

    segment_descriptions = [
        SegmentDescription(**sd) for sd in segment_descriptions
    ]

    seg_series_instance_uid = generate_uid(
        entropy_srcs=[
            study_instance_uid,
            content_description,
            str(seed),
        ]
    )

    prefix = (
        ".".join(seg_series_instance_uid.split(".")[:4]) + "."
    )  # ugly syntax for strap the prefix from the series uid and reuse it for slice identifier but w/e
    seg_sop_instance_uid = generate_uid(
        prefix=prefix,
        entropy_srcs=[patient_id, study_instance_uid, seg_series_instance_uid, str(series_number), str(seed)],
    )
    seg_dcm = Segmentation(
        series_number=series_number,
        sop_instance_uid=seg_sop_instance_uid,
        instance_number=1,
        source_images=dcm_slices,
        pixel_array=seg_np.astype(np.uint8),
        segment_descriptions=segment_descriptions,
        series_instance_uid=seg_series_instance_uid,
        content_description=content_description,
        content_creator_name=content_creator_name,
        content_label=content_label,
        manufacturer=manufacturer,
        manufacturer_model_name=manufacturer_model_name,
        device_serial_number=device_serial_number,
        segmentation_type=segmentation_type,
        software_versions=software_versions,
        # fractional_type=fractional_type
    )
    return seg_dcm