# Defined templates for annotation data-structures
#
# The following template search hierarchial for the definition in the "struct" categories and
# add the information of the leave element based on the content value type:
#
#        "Qualitative": "CODE",
#        "Quantitative": "NUM",
#        "Point": "SCOORD", "SCOORD3D",
#        "UnstructuredText": "TEXT",
#
# Additionally constrains, like specific code values can be included in the constrains-field as list.

sr_template = {
    "1500": {
        "Qualitative": [
            {
                "struct": [
                    {"value": "126010", "scheme_designator": "DCM"},
                    {"value": "125007", "scheme_designator": "DCM"},
                ],
                "constrains": [],
            }
        ],
        "Quantitative": [
            {
                "struct": [
                    {"value": "126010", "scheme_designator": "DCM"},
                    {"value": "125007", "scheme_designator": "DCM"},
                ]
            }
        ],
        "Point": [
            {
                "struct": [
                    {"value": "126010", "scheme_designator": "DCM"},
                    {"value": "125007", "scheme_designator": "DCM"},
                ]
            }
        ],
    },
    "3700": {
        "Qualitative": [{"struct": [], "constrains": []}],
    },
    "3927": {
        "UnstructuredText": [{"struct": []}],
    },
}
