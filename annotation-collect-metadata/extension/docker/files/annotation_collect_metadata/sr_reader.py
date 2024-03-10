from typing import List, Union, Optional

import pydicom
from pydicom.sr.coding import Code
import json
from annotation_collect_metadata.annotation_meta_templates import sr_template


class SR_Reader:

    codecs = {
        "Qualitative": ["CODE"],
        "Quantitative": ["NUM"],
        "Point": ["SCOORD", "SCOORD3D"],
        "UnstructuredText": ["TEXT"],
    }
    mappings = {
        "Qualitative": None,
        "Quantitative": "float",
        "Point": None,
        "UnstructuredText": "text",
    }

    @staticmethod
    def extract_template_data(data: pydicom.Dataset):
        template_id = data.ContentTemplateSequence[0].TemplateIdentifier
        template_dict = SR_Reader.get_template_id(template_id)
        meta_data = dict()
        meta_data["99999999 ContentKey_keyword"] = data.ConceptNameCodeSequence[
            0
        ].CodeMeaning

        for key, values in template_dict.items():
            for value in values:
                filter_codec = SR_Reader.codecs[key]
                nested_filters = SR_Reader.gen_filter_codes(value.get("struct"))
                filter_constraints = SR_Reader.gen_filter_codes(value.get("constrains"))
                sr_sequence = filter_structured_report(
                    data,
                    filter_types=filter_codec,
                    nested_path=nested_filters,
                    type_constraints=filter_constraints,
                )

                key_elements, value_elements = SR_Reader.extract_values(
                    sr_sequence, filter_codec
                )

                meta_data[SR_Reader.generate_keyword(key + "Key_keyword")] = (
                    key_elements
                )

                # HACK to have not undefiend values in opensearch
                mapping = (
                    SR_Reader.mappings[key]
                    if SR_Reader.mappings[key] is not None
                    else "keyword"
                )
                if key == "UnstructuredText":
                    meta_data[SR_Reader.generate_keyword(key + "Value_" + mapping)] = ""

                if len(value_elements) > 0:
                    meta_data[SR_Reader.generate_keyword(key + "Value_" + mapping)] = (
                        value_elements
                    )
                    if mapping == "text":
                        meta_data[
                            SR_Reader.generate_keyword(key + "Value_" + mapping)
                        ] = value_elements[0]

        return meta_data

    @staticmethod
    def get_template_id(template_id: str) -> dict:
        template_dict = sr_template.get(template_id)

        if template_dict:
            return template_dict
        else:
            raise (
                "Template with id:",
                template_id,
                "is not supported. Please define the template in the annotations file.",
            )

    @staticmethod
    def gen_filter_codes(codes_definitions: List[dict]):
        filter_list = list()

        if codes_definitions is None:
            return filter_list

        for value in codes_definitions:
            code = Code(
                value=value["value"],
                scheme_designator=value["scheme_designator"],
                meaning=value.get("meaning"),
            )
            filter_list.append(code)

        return filter_list

    @staticmethod
    def extract_values(seq_data: pydicom.Dataset, codecs: List[str]):
        key_fields = list()
        value_fields = list()

        for element in seq_data:
            value_type = element.get("ValueType")
            if value_type in codecs:
                key_fields.append(element.ConceptNameCodeSequence[0].CodeMeaning)

                if value_type not in ["SCOORD", "SCOORD3D"]:
                    value = None
                    if value_type == "CODE":
                        value = element.ConceptCodeSequence[0].CodeMeaning

                    elif value_type == "TEXT":
                        value = element.TextValue

                    elif value_type == "NUM":
                        value = float(element.MeasuredValueSequence[0].NumericValue)

                    else:
                        raise (value_type, "is not supported type for SR values")

                    if value is not None:
                        value_fields.append(value)

        return key_fields, value_fields

    @staticmethod
    def generate_keyword(keyword: str):
        keyword_name = "99999999 " + keyword
        return keyword_name


def filter_structured_report(
    SR: pydicom.Dataset,
    filter_types: Union[str, List[str]],
    nested_path=List[Code],
    type_constraints: Optional[List[Code]] = None,
):
    code_condition = (
        lambda x, code: x.ConceptNameCodeSequence[0].CodeValue == code.value
    )

    if isinstance(filter_types, str):
        filter_types = [filter_types]

    sr_nested = [SR]
    for q in nested_path:
        for sr in sr_nested:
            sr_nested = [
                x
                for x in sr.ContentSequence
                if x.ConceptNameCodeSequence[0].CodeValue == q.value
            ]

    filtered_elements = []
    for sr in sr_nested:
        elements = [x for x in sr.ContentSequence if x.ValueType in filter_types]
        filtered_elements.extend(elements)

    if type_constraints is not None and len(type_constraints) > 0:
        filtered_elements = [
            q
            for q in filtered_elements
            if any([code_condition(q, c) for c in type_constraints])
        ]

    return filtered_elements
