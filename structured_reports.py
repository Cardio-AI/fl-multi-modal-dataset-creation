"""DICOM structured reporting templates."""
from typing import Optional, Sequence, Union
import datetime

from pydicom.sr.coding import Code
from pydicom.sr.codedict import codes
from pydicom.valuerep import DT

from highdicom.sr.coding import CodedConcept

from highdicom.sr.enum import (
    RelationshipTypeValues,
)
from highdicom.sr.value_types import (
    CodeContentItem,
    ContainerContentItem,
    ContentSequence,
    ImageContentItem,
    NumContentItem,
    PnameContentItem,
    TcoordContentItem,
    TextContentItem,
    DateTimeContentItem,
    CompositeContentItem,
    UIDRefContentItem,
    WaveformContentItem
)
from highdicom.sr.templates import (
    AlgorithmIdentification,
    ObserverContext,
    PersonObserverIdentifyingAttributes,
    Template,
    ObservationContext,
    LanguageOfContentItemAndDescendants
)


class ConcernType(CodeContentItem):
    """:dcm:`CID 3769 <part16/sect_CID_3769.html>`
    Concern Type
    """

    def __init__(
        self,
        type: Union[Code, CodedConcept],
        value: Union[Code, CodedConcept],
        datetime_started: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_problem_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[Union[Code, CodedConcept]] = None
    ) -> None:
        super().__init__(
            name=type,
            value=value,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
        )
        content = ContentSequence()
        if datetime_started is not None:
            datetime_started_item = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernResolved,
                value=datetime_started,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(datetime_started_item)

        if datetime_problem_resolved is not None:
            datetime_problem_resolved_item = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernResolved,
                value=datetime_problem_resolved,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(datetime_problem_resolved_item)
        if status is not None:
            status_item = CodeContentItem(
                name=Code('33999-4', 'LN', 'Status'),  # codes.LN.Status
                value=status
            )
            content.append(status_item)
        if severity is not None:
            severity_item = CodeContentItem(
                name=codes.SCT.Severity,
                value=severity,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(severity_item)
        if stage is not None:
            stage_item = CodeContentItem(
                name=codes.SCT.Stage,
                value=stage,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(stage_item)
        if len(content) > 0:
            self.ContentSequence = content


class Therapy(CodeContentItem):
    """:sct:`277132007`
    Therapy
    """

    def __init__(self,
                 value: Union[Code, CodedConcept],
                 status: Optional[Union[Code, CodedConcept]] = None) -> None:
        super().__init__(
            name=CodedConcept(
                value='277132007',
                meaning='Therapy',
                scheme_designator='SCT'
            ),
            value=value,
            relationship_type=RelationshipTypeValues.CONTAINS)
        content = ContentSequence()
        if status is not None:
            status_item = CodeContentItem(
                name=CodedConcept(
                    value='33999-4',
                    meaning='Status',
                    scheme_designator='LN'
                ),
                value=status,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(status_item)
        if len(content) > 0:
            self.ContentSequence = content


class ClinicalReport(CompositeContentItem):
    """:sct:`371524004`
    Clinical Report
    """

    def __init__(self,
                 document_title: Optional[Union[CodedConcept, Code]] = None
                 ) -> None:
        super().__init__(
            name=codes.SCT.ClinicalReport,
            # TODO: What SOP to use here since Clinical Report is Snowmed?
            # referenced_sop_class_uid="",
            # referenced_sop_instance_uid="",
            relationship_type=RelationshipTypeValues.HAS_PROPERTIES
        )
        content = ContentSequence()
        if document_title is not None:
            document_title_item = CodeContentItem(
                name=codes.DCM.DocumentTitle,
                value=document_title,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(document_title_item)
        if len(content) > 0:
            self.ContentSequence = content


class ProblemProperties(Template):
    """:dcm:`TID 3829 <part16/sect_TID_3829.html>`
    Problem Properties
    """

    def __init__(
        self,
        concern_type: ConcernType,
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        health_status: Optional[Union[Code, CodedConcept]] = None,
        therapies: Optional[Sequence[Therapy]] = None,
        comment: Optional[str] = None
    ):
        item = ContainerContentItem(
            name=codes.DCM.Concern,
            template_id='3829'
        )
        content = ContentSequence()
        if not isinstance(concern_type, ConcernType):
            raise TypeError('Argument "concern_type" must have type ConcernType.')
        content.append(concern_type)
        if datetime_concern_noted is not None:
            datetime_concern_noted_item = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernNoted,
                value=datetime_concern_noted,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(datetime_concern_noted_item)
        if datetime_concern_resolved is not None:
            datetime_concern_resolved_item = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernResolved,
                value=datetime_concern_resolved,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(datetime_concern_resolved_item)
        if health_status is not None:
            health_status_item = CodeContentItem(
                name=codes.LN.HealthStatus,
                value=health_status,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(health_status_item)
        if therapies is not None:
            if not isinstance(therapies, (list, tuple, set)):
                raise TypeError(
                    'Argument "therapies" must be a sequence.'
                )
            for therapy in therapies:
                if not isinstance(therapy, Therapy):
                    raise TypeError(
                        'Items of argument "therapy" must have type Therapy.'
                    )
                content.append(therapy)
        if comment is not None:
            comment_item = TextContentItem(
                name=codes.DCM.Comment,
                value=comment,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(comment_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ProblemList(Template):
    """:ln:`11450-4`
    Problem List
    """

    def __init__(self,
                 concern_types: Optional[Sequence[str]] = None,
                 # TODO: Maybe make these parameters each its own type with preset parameters?
                 cardiac_patient_risk_factors: Optional[Sequence[ProblemProperties]] = None,
                 history_of_diabetes_mellitus: Optional[ProblemProperties] = None,
                 history_of_hypertension: Optional[ProblemProperties] = None,
                 history_of_hypercholesterolemia: Optional[ProblemProperties] = None,
                 arrhythmia: Optional[ProblemProperties] = None,
                 history_of_myocardial_infarction: Optional[ProblemProperties] = None,
                 history_of_kidney_disease: Optional[ProblemProperties] = None) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='11450-4',
                meaning='Problem List',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if concern_types is not None:
            if not isinstance(concern_types, (list, tuple, set)):
                raise TypeError(
                    'Argument "concern_types" must be a sequence.'
                )
            for concern_type in concern_types:
                if not isinstance(concern_type, str):
                    raise TypeError(
                        'Items of argument "concern_types" must have type str.'
                    )
                concern_type_item = TextContentItem(
                    name=CodedConcept(
                        value='3769',
                        meaning='Concern Type',
                        scheme_designator='CID'
                    ),
                    value=concern_type,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(concern_type_item)
        if cardiac_patient_risk_factors is not None:
            if not isinstance(cardiac_patient_risk_factors, (list, tuple, set)):
                raise TypeError(
                    'Argument "cardiac_patient_risk_factors" must be a sequence.'
                )
            for cardiac_patient_risk_factor in cardiac_patient_risk_factors:
                if not isinstance(cardiac_patient_risk_factor, ProblemProperties):
                    raise TypeError(
                        'Items of argument "cardiac_patient_risk_factors" must have type ProblemProperties.'
                    )
                content.extend(cardiac_patient_risk_factor)
        if history_of_diabetes_mellitus is not None:
            if not isinstance(history_of_diabetes_mellitus, ProblemProperties):
                raise TypeError(
                    'Argument "history_of_diabetes_mellitus" must be a ProblemProperties.'
                )
            content.extend(history_of_diabetes_mellitus)
        if history_of_hypertension is not None:
            if not isinstance(history_of_hypertension, ProblemProperties):
                raise TypeError(
                    'Argument "history_of_hypertension" must be a ProblemProperties.'
                )
            content.extend(history_of_hypertension)
        if history_of_hypercholesterolemia is not None:
            if not isinstance(history_of_hypercholesterolemia, ProblemProperties):
                raise TypeError(
                    'Argument "history_of_hypercholesterolemia" must be a ProblemProperties.'
                )
            content.extend(history_of_hypercholesterolemia)
        if arrhythmia is not None:
            if not isinstance(arrhythmia, ProblemProperties):
                raise TypeError(
                    'Argument "arrhythmia" must be a ProblemProperties.'
                )
            content.extend(arrhythmia)
        if history_of_myocardial_infarction is not None:
            if not isinstance(history_of_myocardial_infarction, ProblemProperties):
                raise TypeError(
                    'Argument "history_of_myocardial_infarction" must be a ProblemProperties.'
                )
            content.extend(history_of_myocardial_infarction)
        if history_of_kidney_disease is not None:
            if not isinstance(history_of_kidney_disease, ProblemProperties):
                raise TypeError(
                    'Argument "history_of_kidney_disease" must be a ProblemProperties.'
                )
            content.extend(history_of_kidney_disease)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ProcedureProperties(Template):
    """:dcm:`TID 3830 <part16/sect_TID_3830.html>`
    Procedure Properties
    """

    def __init__(self,
                 name: Union[CodedConcept, Code],
                 value: Union[CodedConcept, Code],
                 procedure_datetime: Optional[Union[str, datetime.datetime, DT]] = None,
                 clinical_reports: Optional[Sequence[ClinicalReport]] = None,
                 clinical_reports_text: Optional[Sequence[str]] = None,
                 service_delivery_location: Optional[str] = None,
                 service_performer_person: Optional[str] = None,
                 service_performer_organisation: Optional[str] = None,
                 comment: Optional[str] = None,
                 procedure_results: Optional[Sequence[Union[Code, CodedConcept]]] = None
                 ) -> None:
        super().__init__()
        item = CodeContentItem(
            name=name,
            value=value,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
        )
        content = ContentSequence()
        if procedure_datetime is not None:
            procedure_datetime_item = DateTimeContentItem(
                name=codes.DCM.ProcedureDatetime,
                value=procedure_datetime,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(procedure_datetime_item)
        if clinical_reports is not None:
            if not isinstance(clinical_reports, (list, tuple, set)):
                raise TypeError(
                    'Argument "clinical_reports" must be a sequence.'
                )
            for clinical_report in clinical_reports:
                if not isinstance(clinical_report, ClinicalReport):
                    raise TypeError(
                        'Items of argument "clinical_reports" must have type ClinicalReport.'
                    )
                content.append(clinical_report)
        if clinical_reports_text is not None:
            if not isinstance(clinical_reports_text, (list, tuple, set)):
                raise TypeError(
                    'Argument "clinical_reports_text" must be a sequence.'
                )
            for clinical_report in clinical_reports_text:
                if not isinstance(clinical_report, str):
                    raise TypeError(
                        'Items of argument "clinical_reports" must have type str.'
                    )
                clinical_report_item = TextContentItem(
                    name=codes.SCT.ClinicalReport,
                    value=clinical_report,
                    relationship_type=RelationshipTypeValues.HAS_PROPERTIES
                )
                content.append(clinical_report_item)
        if service_delivery_location is not None:
            service_delivery_location_item = DateTimeContentItem(
                name=codes.DCM.ServiceDeliveryLocation,
                value=service_delivery_location,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(service_delivery_location_item)
        if service_performer_person is not None:
            service_performer_person_item = PnameContentItem(
                name=codes.DCM.ServicePerformer,
                value=service_performer_person,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(service_performer_person_item)
        if service_performer_organisation is not None:
            service_performer_organisation_item = TextContentItem(
                name=codes.DCM.ServicePerformer,
                value=service_performer_organisation,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(service_performer_organisation_item)
        if comment is not None:
            comment_item = TextContentItem(
                name=codes.DCM.Comment,
                value=comment,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(comment_item)
        if procedure_results is not None:
            if not isinstance(procedure_results, (list, tuple, set)):
                raise TypeError(
                    'Argument "procedure_results" must be a sequence.'
                )
            for procedure_result in procedure_results:
                if not isinstance(procedure_result, (Code, CodedConcept)):
                    raise TypeError(
                        'Items of argument "clinical_reports" must have type Code or CodedConcept.'
                    )
                procedure_result_item = CodeContentItem(
                    name=codes.DCM.ProcedureResult,
                    value=procedure_result,
                    relationship_type=RelationshipTypeValues.HAS_PROPERTIES
                )
                content.append(procedure_result_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class SocialHistory(Template):
    """:ln:`29762-2`
    Social History
    """

    def __init__(self,
                 social_history: Optional[str] = None,
                 social_histories: Optional[Sequence[str]] = None,
                 tobacco_smoking_behavior: Optional[Union[Code, CodedConcept]] = None,
                 drug_misuse_behavior: Optional[Union[Code, CodedConcept]] = None,
                 ) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='29762-2',
                meaning='Social History',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if social_history is not None:
            social_history_item = TextContentItem(
                name=CodedConcept(
                    value='160476009',
                    meaning='Social History',
                    scheme_designator='SCT'
                ),
                value=social_history,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(social_history_item)
        if social_histories is not None:
            if not isinstance(social_histories, (list, tuple, set)):
                raise TypeError(
                    'Argument "social_histories" must be a sequence.'
                )
            for history in social_histories:
                if not isinstance(history, str):
                    raise TypeError(
                        'Items of argument "social_histories" must have type str.'
                    )
                social_history_item = TextContentItem(
                    name=CodedConcept(
                        value='3774',
                        meaning='Social History',
                        scheme_designator='CID'
                    ),
                    value=history,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(social_history_item)
        if tobacco_smoking_behavior is not None:
            tobacco_smoking_behavior_item = CodeContentItem(
                name=codes.SCT.TobaccoSmokingBehavior,
                value=tobacco_smoking_behavior,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(tobacco_smoking_behavior_item)
        if drug_misuse_behavior is not None:
            drug_misuse_behavior_item = CodeContentItem(
                name=codes.SCT.DrugMisuseBehavior,
                value=drug_misuse_behavior,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(drug_misuse_behavior_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class PastSurgicalHistory(Template):
    """:ln:`10167-5`
    Past Surgical History
    """

    def __init__(self,
                 histories: Optional[Sequence[str]] = None,
                 procedure_properties: Optional[Sequence[ProcedureProperties]] = None
                 ) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='10167-5',
                meaning='Past Surgical History',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if histories is not None:
            if not isinstance(histories, (list, tuple, set)):
                raise TypeError(
                    'Argument "histories" must be a sequence.'
                )
            for history in histories:
                if not isinstance(history, str):
                    raise TypeError(
                        'Items of argument "social_histories" must have type str.'
                    )
                history_item = TextContentItem(
                    name=codes.LN.History,
                    value=history,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(history_item)
        if procedure_properties is not None:
            if not isinstance(procedure_properties, (list, tuple, set)):
                raise TypeError(
                    'Argument "procedure_properties" must be a sequence.'
                )
            for procedure_property in procedure_properties:
                if not isinstance(procedure_property, ProcedureProperties):
                    raise TypeError(
                        'Items of argument "procedure_properties" must have type ProcedureProperties.'
                    )
                content.extend(procedure_property)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class RelevantDiagnosticTestsAndOrLaboratoryData(Template):
    """:ln:`30954-2`
    Relevant Diagnostic Tests and/or Laboratory Data
    """

    def __init__(self,
                 histories: Optional[Sequence[str]] = None,
                 procedure_properties: Optional[Sequence[ProcedureProperties]] = None,
                 cholesterol_in_HDL: Optional[float] = None,
                 cholesterol_in_LDL: Optional[float] = None
                 ) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=codes.LN.RelevantDiagnosticTestsAndOrLaboratoryData,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if histories is not None:
            if not isinstance(histories, (list, tuple, set)):
                raise TypeError(
                    'Argument "histories" must be a sequence.'
                )
            for history in histories:
                if not isinstance(history, str):
                    raise TypeError(
                        'Items of argument "social_histories" must have type str.'
                    )
                history_item = TextContentItem(
                    name=codes.LN.History,
                    value=history,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(history_item)
        if procedure_properties is not None:
            if not isinstance(procedure_properties, (list, tuple, set)):
                raise TypeError(
                    'Argument "procedure_properties" must be a sequence.'
                )
            for procedure_property in procedure_properties:
                if not isinstance(procedure_property, ProcedureProperties):
                    raise TypeError(
                        'Items of argument "procedure_properties" must have type ProcedureProperties.'
                    )
                content.extend(procedure_property)
        if cholesterol_in_HDL is not None:
            cholesterol_in_HDL_item = NumContentItem(
                name=CodedConcept(
                    value='2086-7',
                    meaning='Cholesterol in HDL',
                    scheme_designator='LN'
                ),
                value=cholesterol_in_HDL,
                unit=codes.UCUM.NoUnits,  # TODO: No Unit UCUM.MilligramPerDeciliter?
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(cholesterol_in_HDL_item)
        if cholesterol_in_LDL is not None:
            cholesterol_in_LDL_item = NumContentItem(
                name=CodedConcept(
                    value='2089-1',
                    meaning='Cholesterol in LDL',
                    scheme_designator='LN'
                ),
                value=cholesterol_in_LDL,
                unit=codes.UCUM.NoUnits,  # TODO: No Unit UCUM.MilligramPerDeciliter?
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(cholesterol_in_LDL_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class MedicationTypeText(TextContentItem):
    """:dcm:`DT 111516 <part16/chapter_D.html#DCM_111516>`
     Medication Type Text
    """

    def __init__(
        self,
        value: str,
        status: Optional[Union[Code, CodedConcept]]
    ) -> None:
        super().__init__(
            name=codes.DCM.MedicationType,
            value=value,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if status is not None:
            status_item = CodeContentItem(
                name=CodedConcept(
                    value='33999-4',
                    meaning='Status',
                    scheme_designator='LN'
                ),
                value=status,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(status_item)
        if len(content) > 0:
            self.ContentSequence = content


class MedicationTypeCode(CodeContentItem):
    """:dcm:`DT 111516 <part16/chapter_D.html#DCM_111516>`
     Medication Type Code
    """

    def __init__(
        self,
        value: Union[Code, CodedConcept],
        dosage: Optional[float],
        status: Optional[Union[Code, CodedConcept]]
    ) -> None:
        super().__init__(
            name=codes.DCM.MedicationType,
            value=value,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if dosage is not None:
            dosage_item = NumContentItem(
                name=codes.SCT.Dosage,
                value=dosage,
                unit=codes.UCUM.NoUnits,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(dosage_item)
        if status is not None:
            status_item = CodeContentItem(
                name=CodedConcept(
                    value='33999-4',
                    meaning='Status',
                    scheme_designator='LN'
                ),
                value=status,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(status_item)
        if len(content) > 0:
            self.ContentSequence = content


class HistoryOfMedicationUse(Template):
    """:ln:`10160-0`
    History of Medication Use
    """

    def __init__(self,
                 medication_types_text: Optional[Sequence[MedicationTypeText]] = None,
                 medication_types_code: Optional[Sequence[MedicationTypeCode]] = None,
                 ) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='10160-0',
                meaning='History of Medication Use',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if medication_types_text is not None:
            if not isinstance(medication_types_text, (list, tuple, set)):
                raise TypeError(
                    'Argument "medication_types_text" must be a sequence.'
                )
            for medication_type_text in medication_types_text:
                if not isinstance(medication_type_text, MedicationTypeText):
                    raise TypeError(
                        'Items of argument "medication_types_text" must have type MedicationTypeText.'
                    )
                content.append(medication_type_text)
        if medication_types_code is not None:
            if not isinstance(medication_types_code, (list, tuple, set)):
                raise TypeError(
                    'Argument "medication_types_code" must be a sequence.'
                )
            for medication_type_code in medication_types_code:
                if not isinstance(medication_type_code, MedicationTypeCode):
                    raise TypeError(
                        'Items of argument "medication_types_code" must have type MedicationTypeCode.'
                    )
                content.append(medication_type_code)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class FamilyHistoryOfClinicalFinding(CodeContentItem):
    """:sct:`416471007`
    Family history of clinical finding
    """

    def __init__(
        self,
        value: Union[Code, CodedConcept],
        subject_relationship: Union[Code, CodedConcept]
    ) -> None:
        super().__init__(
            name=codes.SCT.FamilyHistoryOfClinicalFinding,
            value=value,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
        )
        content = ContentSequence()
        subject_relationship_item = CodeContentItem(
            name=CodedConcept(
                value='408732007',
                meaning='Subject relationship',
                scheme_designator='SCT'
            ),
            value=subject_relationship,
            relationship_type=RelationshipTypeValues.HAS_PROPERTIES
        )
        content.append(subject_relationship_item)
        if len(content) > 0:
            self.ContentSequence = content


class HistoryOfFamilyMemberDiseases(Template):
    """:ln:`10157-6`
    History of Family Member Diseases
    """

    def __init__(self,
                 histories: Optional[Sequence[str]] = None,
                 family_histories_of_clinical_findings: Optional[Sequence[FamilyHistoryOfClinicalFinding]] = None) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='10157-6',
                meaning='History of Family Member Diseases',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if histories is not None:
            if not isinstance(histories, (list, tuple, set)):
                raise TypeError(
                    'Argument "histories" must be a sequence.'
                )
            for history in histories:
                if not isinstance(history, str):
                    raise TypeError(
                        'Items of argument "social_histories" must have type str.'
                    )
                history_item = TextContentItem(
                    name=codes.LN.History,
                    value=history,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(history_item)
        if family_histories_of_clinical_findings is not None:
            if not isinstance(family_histories_of_clinical_findings, (list, tuple, set)):
                raise TypeError(
                    'Argument "family_histories_of_clinical_findings" must be a sequence.'
                )
            for family_history_of_clinical_finding in family_histories_of_clinical_findings:
                if not isinstance(family_history_of_clinical_finding, FamilyHistoryOfClinicalFinding):
                    raise TypeError(
                        'Items of argument "family_histories_of_clinical_findings" must have type FamilyHistoryOfClinicalFinding.'
                    )
                content.append(family_history_of_clinical_finding)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class MedicalDeviceUse(Template):
    """:dcm:`CID 3831 <part16/sect_TID_3831.html>`
    Medical Device Use
    """

    def __init__(self,
                 datetime_started: Optional[Union[str, datetime.datetime, DT]] = None,
                 datetime_ended: Optional[Union[str, datetime.datetime, DT]] = None,
                 status: Optional[Union[Code, CodedConcept]] = None,
                 comment: Optional[str] = None,
                 ) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='46264-8',
                meaning='Medical Device use',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if datetime_started is not None:
            datetime_started_item = DateTimeContentItem(
                name=codes.DCM.DatetimeStarted,
                value=datetime_started,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(datetime_started_item)
        if datetime_ended is not None:
            datetime_ended_item = DateTimeContentItem(
                name=codes.DCM.DatetimeEnded,
                value=datetime_ended,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(datetime_ended_item)
        if status is not None:
            status_item = CodeContentItem(
                name=CodedConcept(
                    value='33999-4',
                    meaning='Status',
                    scheme_designator='LN'
                ),
                value=status,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(status_item)
        if comment is not None:
            comment_item = TextContentItem(
                name=codes.DCM.Comment,
                value=comment,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(comment_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class HistoryOfMedicalDeviceUse(Template):
    """:ln:`46264-8`
    History of medical device use
    """

    def __init__(self,
                 history: Optional[str] = None,
                 medical_device_uses: Optional[Sequence[MedicalDeviceUse]] = None,
                 ) -> None:
        super().__init__()
        item = ContainerContentItem(
            name=CodedConcept(
                value='46264-8',
                meaning='History of medical device use',
                scheme_designator='LN'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if history is not None:
            history_item = TextContentItem(
                name=codes.LN.History,
                value=history,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(history_item)
        if medical_device_uses is not None:
            if not isinstance(medical_device_uses, (list, tuple, set)):
                raise TypeError(
                    'Argument "medical_device_uses" must be a sequence.'
                )
            for medical_device_use in medical_device_uses:
                if not isinstance(medical_device_use, MedicalDeviceUse):
                    raise TypeError(
                        'Items of argument "medical_device_uses" must have type MedicalDeviceUse.'
                    )
                content.extend(medical_device_use)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class CardiovascularPatientHistory(Template):
    """:dcm:`TID 3802 <part16/sect_TID_3802.html>`
    Cardiovascular Patient History
    """

    def __init__(
        self,
        history: Optional[str] = None,
        problem_list: Optional[ProblemList] = None,
        social_history: Optional[SocialHistory] = None,
        past_surgical_history: Optional[PastSurgicalHistory] = None,
        relevant_diagnostic_tests_and_or_laboratory_data: Optional[RelevantDiagnosticTestsAndOrLaboratoryData] = None,
        history_of_medication_use: Optional[HistoryOfMedicationUse] = None,
        history_of_family_member_diseases: Optional[HistoryOfFamilyMemberDiseases] = None,
        history_of_medical_device_use: Optional[HistoryOfMedicalDeviceUse] = None
    ) -> None:
        item = ContainerContentItem(
            name=codes.LN.History,
            template_id='3802'
        )
        content = ContentSequence()
        if history is not None:
            history_item = TextContentItem(
                name=codes.LN.History,
                value=history,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(history_item)
        if problem_list is not None:
            if not isinstance(problem_list, ProblemList):
                raise TypeError(
                    'Argument "problem_list" must be a ProblemList.'
                )
            content.extend(problem_list)
        if social_history is not None:
            if not isinstance(social_history, SocialHistory):
                raise TypeError(
                    'Argument "social_history" must be a SocialHistory.'
                )
            content.extend(social_history)
        if past_surgical_history is not None:
            if not isinstance(past_surgical_history, PastSurgicalHistory):
                raise TypeError(
                    'Argument "past_surgical_history" must be a PastSurgicalHistory.'
                )
            content.extend(past_surgical_history)
        if relevant_diagnostic_tests_and_or_laboratory_data is not None:
            if not isinstance(relevant_diagnostic_tests_and_or_laboratory_data, RelevantDiagnosticTestsAndOrLaboratoryData):
                raise TypeError(
                    'Argument "relevant_diagnostic_tests_and_or_laboratory_data" must be a RelevantDiagnosticTestsAndOrLaboratoryData.'
                )
            content.extend(relevant_diagnostic_tests_and_or_laboratory_data)
        if history_of_medication_use is not None:
            if not isinstance(history_of_medication_use, HistoryOfMedicationUse):
                raise TypeError(
                    'Argument "history_of_medication_use" must be a HistoryOfMedicationUse.'
                )
            content.extend(history_of_medication_use)
        if history_of_family_member_diseases is not None:
            if not isinstance(history_of_family_member_diseases, HistoryOfFamilyMemberDiseases):
                raise TypeError(
                    'Argument "history_of_family_member_diseases" must be a HistoryOfFamilyMemberDiseases.'
                )
            content.extend(history_of_family_member_diseases)
        if history_of_medical_device_use is not None:
            if not isinstance(history_of_medical_device_use, HistoryOfMedicalDeviceUse):
                raise TypeError(
                    'Argument "history_of_medical_device_use" must be a HistoryOfMedicalDeviceUse.'
                )
            content.extend(history_of_medical_device_use)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class PatientCharacteristicsForECG(Template):
    """:dcm:`TID 3704 <part16/sect_TID_3704.html>`
    Patient Characteristics for ECG
    """

    def __init__(
        self,
        subject_age: int,  # TODO: What type is this number?
        subject_sex: str,
        patient_height: Optional[float] = None,
        patient_weight: Optional[float] = None,
        systolic_blood_pressure: Optional[float] = None,
        diastolic_blood_pressure: Optional[float] = None,
        patient_state: Optional[Union[Code, CodedConcept]] = None,
        pacemaker_in_situ: Optional[Union[Code, CodedConcept]] = None,
        icd_in_situ: Optional[Union[Code, CodedConcept]] = None,
    ):
        item = ContainerContentItem(
            name=codes.DCM.PatientCharacteristics,
            template_id='3704'
        )
        content = ContentSequence()
        if not isinstance(subject_age, int):
            raise TypeError(
                'Argument "subject_age" must have type int.'
            )
        subject_age_item = NumContentItem(
            name=codes.DCM.SubjectAge,
            value=subject_age,
            unit=CodedConcept(
                value='7456',
                meaning='Age Unit',
                scheme_designator='CID'
            ),
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(subject_age_item)
        if not isinstance(subject_sex, str):
            raise TypeError(
                'Argument "subject_sex" must have type str.'
            )
        subject_sex_item = TextContentItem(
            name=codes.DCM.SubjectSex,
            value=subject_sex,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(subject_sex_item)
        if patient_height is not None:
            if not isinstance(patient_height, float):
                raise TypeError(
                    'Argument "patient_height" must have type float.'
                )
            patient_height_item = NumContentItem(
                name=CodedConcept(
                    value='8302-2',
                    meaning='Patient Height',
                    scheme_designator='LN'
                ),
                value=patient_height,
                unit=codes.UCUM.cm,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(patient_height_item)
        if patient_weight is not None:
            if not isinstance(patient_weight, float):
                raise TypeError(
                    'Argument "patient_weight" must have type float.'
                )
            patient_weight_item = NumContentItem(
                name=CodedConcept(
                    value='29463-7',
                    meaning='Patient Weight',
                    scheme_designator='LN'
                ),
                value=patient_weight,
                unit=codes.UCUM.NoUnits,  # TODO: No Unit UCUM.kg?
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(patient_weight_item)
        if systolic_blood_pressure is not None:
            if not isinstance(systolic_blood_pressure, float):
                raise TypeError(
                    'Argument "systolic_blood_pressure" must have type float.'
                )
            systolic_blood_pressure_item = NumContentItem(
                name=codes.SCT.SystolicBloodPressure,
                value=systolic_blood_pressure,
                unit=CodedConcept(
                    value='3500',
                    meaning='Pressure Unit',
                    scheme_designator='CID'
                ),
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(systolic_blood_pressure_item)
        if diastolic_blood_pressure is not None:
            if not isinstance(diastolic_blood_pressure, float):
                raise TypeError(
                    'Argument "diastolic_blood_pressure" must have type float.'
                )
            diastolic_blood_pressure_item = NumContentItem(
                name=codes.SCT.DiastolicBloodPressure,
                value=diastolic_blood_pressure,
                unit=CodedConcept(
                    value='3500',
                    meaning='Pressure Unit',
                    scheme_designator='CID'
                ),
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(diastolic_blood_pressure_item)
        if patient_state is not None:
            if not isinstance(patient_state, (CodedConcept, Code)):
                raise TypeError(
                    'Argument "patient_state" must have type Code or CodedConcept.'
                )
            patient_state_item = CodeContentItem(
                name=codes.DCM.PatientState,
                value=patient_state,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(patient_state_item)
        if pacemaker_in_situ is not None:
            if not isinstance(pacemaker_in_situ, (CodedConcept, Code)):
                raise TypeError(
                    'Argument "pacemaker_in_situ" must have type Code or CodedConcept.'
                )
            pacemaker_in_situ_item = CodeContentItem(
                name=CodedConcept(
                    value='441509002',
                    meaning='Pacemaker in situ',
                    scheme_designator='SCT'
                ),
                value=pacemaker_in_situ,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(pacemaker_in_situ_item)
        if icd_in_situ is not None:
            if not isinstance(icd_in_situ, (CodedConcept, Code)):
                raise TypeError(
                    'Argument "icd_in_situ" must have type Code or CodedConcept.'
                )
            icd_in_situ_item = CodeContentItem(
                name=CodedConcept(
                    value='443325000',
                    meaning='ICD in situ',
                    scheme_designator='SCT'
                ),
                value=icd_in_situ,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(icd_in_situ_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class PriorECGStudy(Template):
    """:dcm:`TID 3702 <part16/sect_TID_3702.html>`
    Prior ECG Study
    """

    def __init__(
        self,
        comparison_with_prior_study_done: Union[CodedConcept, Code],
        procedure_datetime: Optional[Union[str, datetime.datetime, DT]] = None,
        procedure_stdy_instance_uid: Optional[UIDRefContentItem] = None,
        prior_report_for_current_patient: Optional[CompositeContentItem] = None,
        # TODO: Way to represent waveform without requiring the whole content item?
        source_of_measurement: Optional[WaveformContentItem] = None
    ):
        item = ContainerContentItem(
            name=codes.LN.PriorProcedureDescriptions,
            template_id='3702'
        )
        content = ContentSequence()
        comparison_with_prior_study_done_item = CodeContentItem(
            name=CodedConcept(
                value='122140',
                meaning='Comparison with Prior Study Done',
                scheme_designator='DCM'
            ),
            value=comparison_with_prior_study_done,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(comparison_with_prior_study_done_item)
        if procedure_datetime is not None:
            if not isinstance(procedure_datetime, (str, datetime.datetime, DT)):
                raise TypeError(
                    'Argument "procedure_datetime" must have type str, datetime.datetime or DT.'
                )
            procedure_datetime_item = DateTimeContentItem(
                name=codes.DCM.ProcedureDatetime,
                value=procedure_datetime,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(procedure_datetime_item)
        if procedure_stdy_instance_uid is not None:
            if not isinstance(procedure_stdy_instance_uid, UIDRefContentItem):
                raise TypeError(
                    'Argument "procedure_stdy_instance_uid" must have type UIDRefContentItem.'
                )
            content.append(procedure_stdy_instance_uid)
        if prior_report_for_current_patient is not None:
            if not isinstance(prior_report_for_current_patient, CompositeContentItem):
                raise TypeError(
                    'Argument "prior_report_for_current_patient" must have type CompositeContentItem.'
                )
            content.append(prior_report_for_current_patient)
        if source_of_measurement is not None:
            if not isinstance(source_of_measurement, WaveformContentItem):
                raise TypeError(
                    'Argument "source_of_measurement" must have type WaveformContentItem.'
                )
            content.append(source_of_measurement)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ECGWaveFormInformation(Template):
    """:dcm:`TID 3708 <part16/sect_TID_3708.html>`
    ECG Waveform Information
    """

    def __init__(
        self,
        procedure_datetime: Union[str, datetime.datetime, DT],
        # TODO: Way to represent waveform without requiring the whole content item?
        source_of_measurement: Optional[WaveformContentItem] = None,
        lead_system: Optional[Union[CodedConcept, Code]] = None,
        acquisition_device_type: Optional[str] = None,
        equipment_identification: Optional[str] = None,
        person_observer_identifying_attributes: Optional[PersonObserverIdentifyingAttributes] = None,
        room_identification: Optional[str] = None,
        ecg_control_numeric_variables: Optional[Sequence[float]] = None,
        ecg_control_text_variables: Optional[Sequence[str]] = None,
        algorithm_identification: Optional[AlgorithmIdentification] = None
    ) -> None:
        item = ContainerContentItem(
            name=codes.LN.CurrentProcedureDescriptions,
            template_id='3708'
        )
        content = ContentSequence()
        procedure_datetime_item = DateTimeContentItem(
            name=codes.DCM.ProcedureDatetime,
            value=procedure_datetime,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(procedure_datetime_item)
        if source_of_measurement is not None:
            if not isinstance(source_of_measurement, WaveformContentItem):
                raise TypeError(
                    'Argument "source_of_measurement" must have type WaveformContentItem.'
                )
            content.append(source_of_measurement)
        if lead_system is not None:
            if not isinstance(lead_system, (CodedConcept, Code)):
                raise TypeError(
                    'Argument "lead_system" must have type Code or CodedConcept.'
                )
            lead_system_item = CodeContentItem(
                name=CodedConcept(
                    value='10:11345',
                    meaning='Lead System',
                    scheme_designator='MDC'
                ),
                value=lead_system,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(lead_system_item)
        if acquisition_device_type is not None:
            if not isinstance(acquisition_device_type, str):
                raise TypeError(
                    'Argument "acquisition_device_type" must have type str.'
                )
            acquisition_device_type_item = TextContentItem(
                name=codes.DCM.AcquisitionDeviceType,
                value=acquisition_device_type,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(acquisition_device_type_item)
        if equipment_identification is not None:
            if not isinstance(equipment_identification, str):
                raise TypeError(
                    'Argument "equipment_identification" must have type str.'
                )
            equipment_identification_item = TextContentItem(
                name=codes.DCM.EquipmentIdentification,
                value=equipment_identification,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(equipment_identification_item)
        if person_observer_identifying_attributes is not None:
            if not isinstance(person_observer_identifying_attributes, PersonObserverIdentifyingAttributes):
                raise TypeError(
                    'Argument "person_observer_identifying_attributes" must have type PersonObserverIdentifyingAttributes.'
                )
            content.extend(person_observer_identifying_attributes)
        if room_identification is not None:
            if not isinstance(room_identification, (list, tuple, set)):
                raise TypeError(
                    'Argument "room_identifications" must be a sequence.'
                )
            room_identification_item = TextContentItem(
                name=codes.DCM.RoomIdentification,
                value=room_identification,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(room_identification_item)
        if ecg_control_numeric_variables is not None:
            if not isinstance(ecg_control_numeric_variables, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_control_numeric_variables" must be a sequence.'
                )
            for ecg_control_numeric_variable in ecg_control_numeric_variables:
                if not isinstance(ecg_control_numeric_variable, float):
                    raise TypeError(
                        'Items of argument "ecg_control_numeric_variable" must have type float.'
                    )
                ecg_control_numeric_variable_item = NumContentItem(
                    name=CodedConcept(
                        value='3690',
                        meaning='ECG Control Numeric Variable',
                        scheme_designator='CID'
                    ),
                    value=ecg_control_numeric_variable,
                    unit=codes.UCUM.NoUnits,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(ecg_control_numeric_variable_item)
        if ecg_control_text_variables is not None:
            if not isinstance(ecg_control_text_variables, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_control_text_variables" must be a sequence.'
                )
            for ecg_control_text_variable in ecg_control_text_variables:
                if not isinstance(ecg_control_text_variable, str):
                    raise TypeError(
                        'Items of argument "ecg_control_numeric_variable" must have type str.'
                    )
                ecg_control_text_variable_item = TextContentItem(
                    name=CodedConcept(
                        value='3691',
                        meaning='ECG Control Text Variable',
                        scheme_designator='CID'
                    ),
                    value=ecg_control_text_variable,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(ecg_control_text_variable_item)
        if algorithm_identification is not None:
            if not isinstance(algorithm_identification, AlgorithmIdentification):
                raise TypeError(
                    'Argument "algorithm_identification" must have type AlgorithmIdentification.'
                )
            content.extend(algorithm_identification)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ECGMeasurementSource(Template):
    """:dcm:`TID 3715 <part16/sect_TID_3715.html>`
    ECG Measurement Source
    """

    def __init__(
        self,
        # TODO: Definition of "TID 3715 ECG Measurement Source" is not in accordance with DICOM documentation
        beat_number: Optional[str],
        measurement_method: Optional[Union[Code, CodedConcept]],
        source_of_measurement: Optional[TcoordContentItem]
        # TODO: Why does DICOM documentation have a "SELECTED FROM" Waveform without a Concept Name?
    ) -> None:
        item = ContainerContentItem(
            # TODO: What name?
            name=CodedConcept(
                value='3715',
                meaning='ECG Measurement Source',
                scheme_designator='TID'
            ),
            template_id='3708'
        )
        content = ContentSequence()
        if not isinstance(beat_number, str):
            raise TypeError(
                'Argument "beat_number" must have type str.'
            )
        beat_number_item = TextContentItem(
            name=codes.DCM.BeatNumber,
            value=beat_number,
            relationship_type=RelationshipTypeValues.CONTAINS  # TODO: No relationship type in DICOM documentation?
        )
        content.append(beat_number_item)
        if source_of_measurement is not None:
            if not isinstance(source_of_measurement, WaveformContentItem):
                raise TypeError(
                    'Argument "source_of_measurement" must have type WaveformContentItem.'
                )
            content.append(source_of_measurement)
        if measurement_method is not None:
            if not isinstance(measurement_method, (Code, CodedConcept)):
                raise TypeError(
                    'Argument "measurement_method" must be a Code or CodedConcept.'
                )
            measurement_method_item = CodeContentItem(
                name=codes.SCT.MeasurementMethod,
                value=measurement_method,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            content.append(measurement_method_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class QTcIntervalGlobal(NumContentItem):
    """:mdc:`DT 2:15876`
    QTc interval global
    """

    def __init__(
        self,
        value: float,
        algorithm_name: Optional[Union[Code, CodedConcept]] = None
    ) -> None:
        super().__init__(
            name=codes.MDC.QtcIntervalGlobal,
            value=value,
            unit=codes.UCUM.Millisecond,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if algorithm_name is not None:
            if not isinstance(algorithm_name, (Code, CodedConcept)):
                raise TypeError(
                    'Argument "algorithm_name" must have type Code or CodedConcept.'
                )
            algorithm_name_item = CodeContentItem(
                name=codes.DCM.AlgorithmName,
                value=algorithm_name,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            content.append(algorithm_name_item)
        if len(content) > 0:
            self.ContentSequence = content


class NumberOfEctopicBeats(NumContentItem):
    """:dcm:`DT 122707`
    Number of Ectopic Beats
    """

    def __init__(
        self,
        value: float,
        associated_morphologies: Optional[Sequence[Union[Code, CodedConcept]]] = None
    ) -> None:
        super().__init__(
            name=codes.MDC.NumberOfEctopicBeats,
            value=value,
            unit=codes.UCUM.NoUnits,  # TODO No Unit UCUM.beats?
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if associated_morphologies is not None:
            if not isinstance(associated_morphologies, (list, tuple, set)):
                raise TypeError(
                    'Argument "associated_morphologies" must be a sequence.'
                )
            for associated_morphology in associated_morphologies:
                if not isinstance(associated_morphology, (Code, CodedConcept)):
                    raise TypeError(
                        'Items of argument "associated_morphology" must have type Code or CodedConcept.'
                    )
                associated_morphology_item = CodeContentItem(
                    name=codes.SCT.AssociatedMorphology,
                    value=associated_morphology,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(associated_morphology_item)
        if len(content) > 0:
            self.ContentSequence = content


class ECGGlobalMeasurements(Template):
    """:dcm:`TID 3713 <part16/sect_TID_3713.html>`
    ECG Global Measurements
    """

    def __init__(
        self,
        ventricular_heart_rate: float,
        qt_interval_global: float,
        pr_interval_global: float,
        qrs_duration_global: float,
        rr_interval_global: float,
        ecg_measurement_source: Optional[ECGMeasurementSource] = None,
        atrial_heart_rate: Optional[float] = None,
        qtc_interval_global: Optional[QTcIntervalGlobal] = None,
        ecg_global_waveform_durations: Optional[Sequence[float]] = None,
        ecg_axis_measurements: Optional[Sequence[float]] = None,
        count_of_all_beats: Optional[float] = None,
        number_of_ectopic_beats: Optional[NumberOfEctopicBeats] = None
    ) -> None:
        item = ContainerContentItem(
            name=codes.DCM.ECGGlobalMeasurements,
            template_id='3713'
        )
        content = ContentSequence()
        if not isinstance(ventricular_heart_rate, float):
            raise TypeError(
                'Argument "ventricular_heart_rate" must have type float.'
            )
        ventricular_heart_rate_item = NumContentItem(
            name=CodedConcept(
                value='2:16016',
                meaning='Ventricular Heart Rate',
                scheme_designator='MDC'
            ),
            value=ventricular_heart_rate,
            unit=codes.UCUM.NoUnits,  # TODO No Unit UCUM.bpm?
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(ventricular_heart_rate_item)
        if not isinstance(qt_interval_global, float):
            raise TypeError(
                'Argument "qt_interval_global" must have type float.'
            )
        qt_interval_global_item = NumContentItem(
            name=codes.MDC.QTIntervalGlobal,
            value=qt_interval_global,
            unit=codes.UCUM.Millisecond,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(qt_interval_global_item)
        if not isinstance(pr_interval_global, float):
            raise TypeError(
                'Argument "qt_interval_global" must have type float.'
            )
        pr_interval_global_item = NumContentItem(
            name=codes.MDC.PRIntervalGlobal,
            value=pr_interval_global,
            unit=codes.UCUM.Millisecond,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(pr_interval_global_item)
        if not isinstance(qrs_duration_global, float):
            raise TypeError(
                'Argument "qrs_duration_global" must have type float.'
            )
        qrs_duration_global_item = NumContentItem(
            name=codes.MDC.QRSDurationGlobal,
            value=qrs_duration_global,
            unit=codes.UCUM.Millisecond,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(qrs_duration_global_item)
        if not isinstance(rr_interval_global, float):
            raise TypeError(
                'Argument "rr_interval_global" must have type float.'
            )
        rr_interval_global_item = NumContentItem(
            name=codes.MDC.RRIntervalGlobal,
            value=rr_interval_global,
            unit=codes.UCUM.Millisecond,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content.append(rr_interval_global_item)
        if ecg_measurement_source is not None:
            if not isinstance(ecg_measurement_source, ECGMeasurementSource):
                raise TypeError(
                    'Argument "ecg_measurement_source" must have type ECGMeasurementSource.'
                )
            content.extend(ecg_measurement_source)
        if atrial_heart_rate is not None:
            if not isinstance(atrial_heart_rate, float):
                raise TypeError(
                    'Argument "atrial_heart_rate" must have type float.'
                )
            atrial_heart_rate_item = NumContentItem(
                name=CodedConcept(
                    value='2:16020',
                    meaning='Atrial Heart Rate',
                    scheme_designator='MDC'
                ),
                value=atrial_heart_rate,
                unit=codes.UCUM.NoUnits,  # TODO No Unit UCUM.bpm?
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(atrial_heart_rate_item)
        if qtc_interval_global is not None:
            if not isinstance(qtc_interval_global, QTcIntervalGlobal):
                raise TypeError(
                    'Argument "qtc_interval_global" must have type QTcIntervalGlobal.'
                )
            content.append(qtc_interval_global)
        if ecg_global_waveform_durations is not None:
            if not isinstance(ecg_global_waveform_durations, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_global_waveform_durations" must be a sequence.'
                )
            for ecg_global_waveform_duration in ecg_global_waveform_durations:
                if not isinstance(ecg_global_waveform_duration, float):
                    raise TypeError(
                        'Items of argument "ecg_global_waveform_duration" must have type float.'
                    )
                ecg_global_waveform_duration_item = NumContentItem(
                    name=CodedConcept(
                        value='3687',
                        meaning='ECG Global Waveform Duration',
                        scheme_designator='CID'
                    ),
                    value=ecg_global_waveform_duration,
                    unit=codes.UCUM.Millisecond,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(ecg_global_waveform_duration_item)
        if ecg_axis_measurements is not None:
            if not isinstance(ecg_axis_measurements, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_axis_measurements" must be a sequence.'
                )
            for ecg_axis_measurement in ecg_axis_measurements:
                if not isinstance(ecg_axis_measurement, float):
                    raise TypeError(
                        'Items of argument "ecg_axis_measurement" must have type float.'
                    )
                ecg_axis_measurement_item = NumContentItem(
                    name=CodedConcept(
                        value='3229',
                        meaning='ECG Axis Measurement',
                        scheme_designator='CID'
                    ),
                    value=ecg_axis_measurement,
                    unit=codes.UCUM.Degree,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(ecg_axis_measurement_item)
        if count_of_all_beats is not None:
            if not isinstance(count_of_all_beats, float):
                raise TypeError(
                    'Argument "count_of_all_beats" must have type float.'
                )
            count_of_all_beats_item = NumContentItem(
                name=CodedConcept(
                    value='2:16032',
                    meaning='Count of all beats',
                    scheme_designator='MDC'
                ),
                value=count_of_all_beats,
                unit=codes.UCUM.NoUnits,  # TODO No Unit UCUM.beats?
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(count_of_all_beats_item)
        if number_of_ectopic_beats is not None:
            if not isinstance(number_of_ectopic_beats, float):
                raise TypeError(
                    'Argument "number_of_ectopic_beats" must have type float.'
                )
            content.append(number_of_ectopic_beats)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ECGLeadMeasurements(Template):
    """:dcm:`TID 3714 <part16/sect_TID_3714.html>`
    ECG Lead Measurements
    """

    def __init__(
        self,
        lead_id: Union[Code, CodedConcept],
        ecg_measurement_source: Optional[ECGMeasurementSource] = None,
        electrophysiology_waveform_durations: Optional[Sequence[float]] = None,
        electrophysiology_waveform_voltages: Optional[Sequence[float]] = None,
        st_segment_finding: Optional[Union[Code, CodedConcept]] = None,
        findings: Optional[Sequence[Union[Code, CodedConcept]]] = None
    ) -> None:
        item = ContainerContentItem(
            name=codes.DCM.ECGLeadMeasurements,
            template_id='3714'
        )
        content = ContentSequence()
        if not isinstance(lead_id, (Code, CodedConcept)):
            raise TypeError(
                'Argument "lead_id" must be a Code or CodedConcept.'
            )
        lead_id_item = CodeContentItem(
            name=codes.DCM.LeadID,
            value=lead_id,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
        )
        content.append(lead_id_item)
        if ecg_measurement_source is not None:
            if not isinstance(ecg_measurement_source, ECGMeasurementSource):
                raise TypeError(
                    'Argument "ecg_measurement_source" must be a ECGMeasurementSource.'
                )
            content.extend(ecg_measurement_source)
        if electrophysiology_waveform_durations is not None:
            if not isinstance(electrophysiology_waveform_durations, (list, tuple, set)):
                raise TypeError(
                    'Argument "electrophysiology_waveform_durations" must be a sequence.'
                )
            for electrophysiology_waveform_duration in electrophysiology_waveform_durations:
                if not isinstance(electrophysiology_waveform_duration, float):
                    raise TypeError(
                        'Items of argument "electrophysiology_waveform_duration" must have type float.'
                    )
                electrophysiology_waveform_duration_item = NumContentItem(
                    name=CodedConcept(
                        value='3687',
                        meaning='Electrophysiology Waveform Duration',
                        scheme_designator='CID'
                    ),
                    value=electrophysiology_waveform_duration,
                    unit=codes.UCUM.Millisecond,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(electrophysiology_waveform_duration_item)
        if electrophysiology_waveform_voltages is not None:
            if not isinstance(electrophysiology_waveform_voltages, (list, tuple, set)):
                raise TypeError(
                    'Argument "electrophysiology_waveform_voltages" must be a sequence.'
                )
            for electrophysiology_waveform_voltage in electrophysiology_waveform_voltages:
                if not isinstance(electrophysiology_waveform_voltage, float):
                    raise TypeError(
                        'Items of argument "electrophysiology_waveform_voltage" must have type float.'
                    )
                electrophysiology_waveform_voltage_item = NumContentItem(
                    name=CodedConcept(
                        value='3687',
                        meaning='Electrophysiology Waveform Duration',
                        scheme_designator='CID'
                    ),
                    value=electrophysiology_waveform_voltage,
                    unit=codes.UCUM.NoUnits,  # TODO No Unit UCUM.MilliVolt?
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(electrophysiology_waveform_voltage_item)
        if st_segment_finding is not None:
            if not isinstance(st_segment_finding, (Code, CodedConcept)):
                raise TypeError(
                    'Argument "st_segment_finding" must be a Code or CodedConcept.'
                )
            st_segment_finding_item = CodeContentItem(
                name=CodedConcept(
                    value='365416000',
                    meaning='ST Segment Finding',
                    scheme_designator='SCT'
                ),
                value=st_segment_finding,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(st_segment_finding_item)
        if findings is not None:
            if not isinstance(findings, (list, tuple, set)):
                raise TypeError(
                    'Argument "findings" must be a sequence.'
                )
            for finding in findings:
                if not isinstance(finding, float):
                    raise TypeError(
                        'Items of argument "finding" must have type float.'
                    )
                finding_item = CodeContentItem(
                    name=codes.DCM.Finding,
                    value=finding,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(finding_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class QuantitativeAnalysis(Template):
    """:dcm:`EV 122144`
    Quantitative Analysis
    """

    def __init__(
        self,
        ecg_global_measurements: Optional[ECGGlobalMeasurements] = None,
        ecg_lead_measurements: Optional[Sequence[ECGLeadMeasurements]] = None,
    ) -> None:
        item = ContainerContentItem(
            name=codes.LN.CurrentProcedureDescriptions,
            template_id='3708'
        )
        content = ContentSequence()
        if ecg_global_measurements is not None:
            if not isinstance(ecg_global_measurements, ECGGlobalMeasurements):
                raise TypeError(
                    'Argument "ecg_global_measurements" must be a ECGGlobalMeasurements.'
                )
            content.extend(ecg_global_measurements)
        if ecg_lead_measurements is not None:
            if not isinstance(ecg_lead_measurements, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_lead_measurements" must be a sequence.'
                )
            for ecg_lead_measurement in ecg_lead_measurements:
                if not isinstance(ecg_lead_measurement, ECGLeadMeasurements):
                    raise TypeError(
                        'Items of argument "ecg_lead_measurement" must have type ECGLeadMeasurements.'
                    )
                content.extend(ecg_lead_measurement)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ECGFinding(Template):
    """:sct:`EV 271921002`
    ECG Finding
    """

    def __init__(
        self,
        value: Union[CodedConcept, Code],
        equivalent_meaning_of_value: Optional[str] = None,
        ecg_findings: Optional["ECGFinding"] = None
    ):
        item = CodeContentItem(
            name=CodedConcept(
                value='271921002',
                meaning='ECG Finding',
                scheme_designator='SCT'
            ),
            value=value,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if equivalent_meaning_of_value is not None:
            if not isinstance(equivalent_meaning_of_value, str):
                raise TypeError(
                    'Argument "equivalent_meaning_of_value" must have type str.'
                )
            equivalent_meaning_of_value_item = TextContentItem(
                name=codes.DCM.EquivalentMeaningOfValue,
                value=equivalent_meaning_of_value,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            content.append(equivalent_meaning_of_value_item)
        if ecg_findings is not None:
            if not isinstance(ecg_findings, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_findings" must be a sequence.'
                )
            for ecg_finding in ecg_findings:
                if not isinstance(ecg_finding, ecg_finding):
                    raise TypeError(
                        'Items of argument "ecg_finding" must have type ECGFinding.'
                    )
                content.append(ecg_finding)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ECGQualitativeAnalysis(Template):
    """:dcm:`TID 3717 <part16/sect_TID_3717.html>`
    ECG Qualitative Analysis
    """

    def __init__(
        self,
        ecg_finding_text: Optional[str] = None,
        ecg_finding_codes: Optional[Sequence[ECGFinding]] = None
    ):
        item = ContainerContentItem(
            name=codes.DCM.QualitativeAnalysis,
            template_id='3717'
        )
        content = ContentSequence()
        if ecg_finding_text is None and ecg_finding_codes is None:
            raise ValueError(
                'Either argument "ecg_finding_text" or "ECG_finding_code" must be given.'
            )
        if ecg_finding_text is not None:
            if not isinstance(ecg_finding_text, str):
                raise TypeError(
                    'Argument "ecg_finding_text" must have type str.'
                )
            ecg_finding_text_item = TextContentItem(
                name=CodedConcept(
                    value='271921002',
                    meaning='ECG Finding',
                    scheme_designator='SCT'
                ),
                value=ecg_finding_text,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(ecg_finding_text_item)
        if ecg_finding_codes is not None:
            if not isinstance(ecg_finding_codes, (list, tuple, set)):
                raise TypeError(
                    'Argument "ecg_finding_code" must be a sequence.'
                )
            for ecg_finding_code in ecg_finding_codes:
                if not isinstance(ecg_finding_code, ECGFinding):
                    raise TypeError(
                        'Items of argument "ecg_finding" must have type ECGFinding.'
                    )
                content.extend(ecg_finding_code)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class SummaryECG(Template):
    """:dcm:`TID 3719 <part16/sect_TID_3719.html>`
    Summary, ECG
    """

    def __init__(
        self,
        summary: Optional[str] = None,
        ecg_overall_finding: Optional[Union[CodedConcept, Code]] = None
    ):
        item = ContainerContentItem(
            name=codes.LN.Summary,
            template_id='3719'
        )
        content = ContentSequence()
        if summary is not None:
            if not isinstance(summary, str):
                raise TypeError(
                    'Argument "summary" must have type str.'
                )
            summary_item = TextContentItem(
                name=codes.LN.Summary,
                value=summary,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(summary_item)
        if ecg_overall_finding is not None:
            if not isinstance(ecg_overall_finding, str):
                raise TypeError(
                    'Argument "ECG_overall_finding" must have type str.'
                )
            ecg_overall_finding_item = CodeContentItem(
                name=CodedConcept(
                    value='18810-2',
                    meaning='ECG overall finding',
                    scheme_designator='LN'
                ),
                value=ecg_overall_finding,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(ecg_overall_finding_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class IndicationsForProcedure(Template):
    """:ln:`EV 18785-6`
    Indications for Procedure
    """

    def __init__(
        self,
        findings: Optional[Sequence[Union[Code, CodedConcept]]] = None,
        finding_text: Optional[str] = None
    ) -> None:
        item = ContainerContentItem(
            name=codes.LN.IndicationsForProcedure
        )
        content = ContentSequence()
        if findings is not None:
            if not isinstance(findings, (list, tuple, set)):
                raise TypeError(
                    'Argument "findings" must be a sequence.'
                )
            for finding in findings:
                if not isinstance(finding, (CodedConcept, Code, )):
                    raise TypeError(
                        'Argument "findings" must have type Code or CodedConcept.'
                    )
                finding_item = CodeContentItem(
                    name=codes.DCM.Finding,
                    value=finding,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                content.append(finding_item)
        if finding_text is not None:
            if not isinstance(finding_text, str):
                raise TypeError(
                    'Argument "finding_text" must have type str.'
                )
            finding_text_item = TextContentItem(
                name=codes.DCM.Finding,
                value=finding_text,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            content.append(finding_text_item)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class ECGReport(Template):
    """:dcm:`TID 3700 <part16/chapter_A.html#sect_TID_3700>`
    ECG Report
    """

    def __init__(
        self,
        language_of_content_item_and_descendants: LanguageOfContentItemAndDescendants,
        observer_contexts: Sequence[ObserverContext],
        ecg_waveform_information: ECGWaveFormInformation,
        quantitative_analysis: QuantitativeAnalysis,
        procedure_reported: Optional[Union[CodedConcept, Code]] = None,
        indications_for_procedure: Optional[IndicationsForProcedure] = None,
        cardiovascular_patient_history: Optional[CardiovascularPatientHistory] = None,
        patient_characteristics_for_ecg: Optional[PatientCharacteristicsForECG] = None,
        prior_ecg_study: Optional[PriorECGStudy] = None,
        ecg_qualitative_analysis: Optional[ECGQualitativeAnalysis] = None,
        summary_ecg: Optional[SummaryECG] = None
    ) -> None:
        item = ContainerContentItem(
            name=codes.LN.ECGReport,
            template_id='3700'
        )
        content = ContentSequence()
        if not isinstance(language_of_content_item_and_descendants, LanguageOfContentItemAndDescendants):
            raise TypeError(
                'Argument "language_of_content_item_and_descendants" must have type LanguageOfContentItemAndDescendants.'
            )
        content.extend(language_of_content_item_and_descendants)
        if not isinstance(observer_contexts, (list, tuple, set)):
            raise TypeError(
                'Argument "observer_contexts" must be a sequence.'
            )
        for observer_context in observer_contexts:
            if not isinstance(observer_context, ObserverContext):
                raise TypeError(
                    'Items of argument "observer_context" must have type ObserverContext.'
                )
            content.extend(observer_context)
        if not isinstance(ecg_waveform_information, ECGWaveFormInformation):
            raise TypeError(
                'Argument "ecg_waveform_information" must have type ECGWaveFormInformation.'
            )
        content.extend(ecg_waveform_information)
        if not isinstance(quantitative_analysis, QuantitativeAnalysis):
            raise TypeError(
                'Argument "quantitative_analysis" must have type QuantitativeAnalysis.'
            )
        content.extend(quantitative_analysis)
        if procedure_reported is not None:
            if not isinstance(procedure_reported, (CodedConcept, Code)):
                raise TypeError(
                    'Argument "procedure_reported" must have type Code or CodedConcept.'
                )
            procedure_reported_item = CodeContentItem(
                name=codes.DCM.ProcedureReported,
                value=procedure_reported,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            content.append(procedure_reported_item)
        if indications_for_procedure is not None:
            if not isinstance(indications_for_procedure, IndicationsForProcedure):
                raise TypeError(
                    'Argument "indications_for_procedure" must have type IndicationsForProcedure.'
                )
            content.extend(indications_for_procedure)
        if cardiovascular_patient_history is not None:
            if not isinstance(cardiovascular_patient_history, CardiovascularPatientHistory):
                raise TypeError(
                    'Argument "cardiovascular_patient_history" must have type CardiovascularPatientHistory.'
                )
            content.append(cardiovascular_patient_history)
        if patient_characteristics_for_ecg is not None:
            if not isinstance(patient_characteristics_for_ecg, PatientCharacteristicsForECG):
                raise TypeError(
                    'Argument "patient_characteristics_for_ecg" must have type PatientCharacteristicsForECG.'
                )
            content.append(patient_characteristics_for_ecg)
        if prior_ecg_study is not None:
            if not isinstance(prior_ecg_study, PriorECGStudy):
                raise TypeError(
                    'Argument "prior_ecg_study" must have type PriorECGStudy.'
                )
            content.append(prior_ecg_study)
        if ecg_qualitative_analysis is not None:
            if not isinstance(ecg_qualitative_analysis, ECGQualitativeAnalysis):
                raise TypeError(
                    'Argument "ecg_qualitative_analysis" must have type ECGQualitativeAnalysis.'
                )
            content.append(ecg_qualitative_analysis)
        if summary_ecg is not None:
            if not isinstance(summary_ecg, SummaryECG):
                raise TypeError(
                    'Argument "summary_ecg" must have type SummaryECG.'
                )
            content.append(summary_ecg)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class LanguageOfValue(CodeContentItem):
    """:dcm:`TID 1201 <part16/chapter_A.html#sect_TID_1201>`
    Language of Value
    """

    def __init__(self,
                 language: Union[Code, CodedConcept],
                 country_of_language: Optional[Union[Code, CodedConcept]] = None
                 ) -> None:
        super().__init__(
            name=codes.DCM.LanguageOfValue,
            value=language,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
        )
        content = ContentSequence()
        if country_of_language is not None:
            country_of_language_item = CodeContentItem(
                name=codes.DCM.CountryOfLanguage,
                value=country_of_language,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            content.append(country_of_language_item)
        if len(content) > 0:
            self.ContentSequence = content


class EquivalentMeaningsOfConceptNameCode(CodeContentItem):
    """:dcm:`TID 1210 <part16/chapter_A.html#sect_TID_1210>`
    Equivalent Meaning(s) of Concept Name Code
    """

    def __init__(self,
                 value: Union[Code, CodedConcept],
                 language_of_value: Optional[LanguageOfValue] = None
                 ) -> None:
        super().__init__(
            name=codes.DCM.EquivalentMeaningOfConceptName,
            value=value,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD)
        content = ContentSequence()
        if language_of_value is not None:
            content.append(language_of_value)
        if len(content) > 0:
            self.ContentSequence = content


class EquivalentMeaningsOfConceptNameText(TextContentItem):
    """:dcm:`TID 1210 <part16/chapter_A.html#sect_TID_1210>`
    Equivalent Meaning(s) of Concept Name Text
    """

    def __init__(self,
                 value: str,
                 language_of_value: Optional[LanguageOfValue] = None
                 ) -> None:
        super().__init__(
            name=codes.DCM.EquivalentMeaningOfConceptName,
            value=value,
            relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD)
        content = ContentSequence()
        if language_of_value is not None:
            content.append(language_of_value)
        if len(content) > 0:
            self.ContentSequence = content


class ReportNarrativeCode(CodeContentItem):
    """:dcm:`TID 2002 <part16/chapter_A.html#sect_TID_2002>`
    Report Narrative Code
    """

    def __init__(self,
                 value: Union[Code, CodedConcept],
                 basic_diagnostic_imaging_report_observations: Optional[Sequence[
                     # TODO: Definition of "TID 2001 Basic Diagnostic Imaging Report Observations" is not in accordance with DICOM documentation
                     ImageContentItem]] = None
                 ) -> None:
        super().__init__(
            name=CodedConcept(
                value='7002',
                meaning='Diagnostic Imaging Report Element',
                scheme_designator='CID'
            ),
            value=value,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if not isinstance(basic_diagnostic_imaging_report_observations, (list, tuple, set)):
            raise TypeError(
                'Argument "basic_diagnostic_imaging_report_observations" must be a sequence.'
            )
        for basic_diagnostic_imaging_report_observation in basic_diagnostic_imaging_report_observations:
            if not isinstance(basic_diagnostic_imaging_report_observation, ImageContentItem):
                raise TypeError(
                    'Items of argument "basic_diagnostic_imaging_report_observation" must have type ImageContentItem.'
                )
            content.append(basic_diagnostic_imaging_report_observation)
        if len(content) > 0:
            self.ContentSequence = content


class ReportNarrativeText(TextContentItem):
    """:dcm:`TID 2002 <part16/chapter_A.html#sect_TID_2002>`
    Report Narrative Text
    """

    def __init__(self,
                 value: str,
                 basic_diagnostic_imaging_report_observations: Optional[Sequence[
                     # TODO: Definition of "TID 2001 Basic Diagnostic Imaging Report Observations" is not in accordance with DICOM documentation
                     ImageContentItem]] = None
                 ) -> None:
        super().__init__(
            name=CodedConcept(
                value='7002',
                meaning='Diagnostic Imaging Report Element',
                scheme_designator='CID'
            ),
            value=value,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        content = ContentSequence()
        if not isinstance(basic_diagnostic_imaging_report_observations, (list, tuple, set)):
            raise TypeError(
                'Argument "basic_diagnostic_imaging_report_observations" must be a sequence.'
            )
        for basic_diagnostic_imaging_report_observation in basic_diagnostic_imaging_report_observations:
            if not isinstance(basic_diagnostic_imaging_report_observation, ImageContentItem):
                raise TypeError(
                    'Items of argument "basic_diagnostic_imaging_report_observation" must have type ImageContentItem.'
                )
            content.append(basic_diagnostic_imaging_report_observation)
        if len(content) > 0:
            self.ContentSequence = content


class DiagnosticImagingReportHeading(Template):
    """:dcm:`TID 7001 <part16/sect_CID_7001.html>`
    Diagnostic Imaging Report Heading
    """

    def __init__(
        self,
        report_narrative: Union[ReportNarrativeCode, ReportNarrativeText],
        observation_context: Optional[ObservationContext] = None
    ):
        item = ContainerContentItem(
            name=CodedConcept(
                value='7001',
                meaning='Diagnostic Imaging Report Heading',
                scheme_designator='CID'
            ),
            template_id='7001'
        )
        content = ContentSequence()
        if not isinstance(report_narrative, (ReportNarrativeCode, ReportNarrativeText)):
            raise TypeError(
                'Argument "report_narrative" must have type ReportNarrativeCode or ReportNarrativeText.'
            )
        content.extend(report_narrative)
        if observation_context is not None:
            if not isinstance(observation_context, ObservationContext):
                raise TypeError(
                    'Argument "observation_context" must have type ObservationContext.'
                )
            content.extend(observation_context)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)


class BasicDiagnosticImagingReport(Template):
    """:dcm:`TID 2000 <part16/chapter_A.html#sect_TID_2000>`
    Basic Diagnostic Imaging Report
    """

    def __init__(
        self,
        language_of_content_item_and_descendants: LanguageOfContentItemAndDescendants,
        observation_context: ObservationContext,
        procedures_reported: Optional[Sequence[Union[CodedConcept, Code]]] = None,
        acquisition_device_types: Optional[Sequence[Union[CodedConcept, Code]]] = None,
        target_regions: Optional[Sequence[Union[CodedConcept, Code]]] = None,
        equivalent_meanings_of_concept_name: Optional[Sequence[Union[EquivalentMeaningsOfConceptNameText,
                                                                     EquivalentMeaningsOfConceptNameCode]]] = None,
        diagnostic_imaging_report_headings: Optional[Sequence[DiagnosticImagingReportHeading]] = None
    ):
        item = ContainerContentItem(
            name=CodedConcept(
                value='2000',
                meaning='Basic Diagnostic Imaging Report',
                scheme_designator='TID'
            ),
            template_id='2000'
        )
        content = ContentSequence()
        if not isinstance(language_of_content_item_and_descendants, LanguageOfContentItemAndDescendants):
            raise TypeError(
                'Argument "language_of_content_item_and_descendants" must have type LanguageOfContentItemAndDescendants.'
            )
        content.extend(language_of_content_item_and_descendants)
        if not isinstance(observation_context, ObservationContext):
            raise TypeError(
                'Argument "observation_context" must have type ObservationContext.'
            )
        content.extend(observation_context)
        if procedures_reported is not None:
            if not isinstance(procedures_reported, (list, tuple, set)):
                raise TypeError(
                    'Argument "procedures_reported" must be a sequence.'
                )
            for procedure_reported in procedures_reported:
                if not isinstance(procedure_reported, (CodedConcept, Code)):
                    raise TypeError(
                        'Items of argument "procedure_reported" must have type Code or CodedConcept.'
                    )
                procedure_reported_item = CodeContentItem(
                    name=codes.DCM.ProcedureReported,
                    value=procedure_reported,
                    relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
                )
                content.append(procedure_reported_item)
        if acquisition_device_types is not None:
            if not isinstance(acquisition_device_types, (list, tuple, set)):
                raise TypeError(
                    'Argument "acquisition_device_types" must be a sequence.'
                )
            for acquisition_device_type in acquisition_device_types:
                if not isinstance(acquisition_device_type, (CodedConcept, Code)):
                    raise TypeError(
                        'Items of argument "acquisition_device_type" must have type Code or CodedConcept.'
                    )
                acquisition_device_type_item = CodeContentItem(
                    name=codes.DCM.AcquisitionDeviceType,
                    value=acquisition_device_type,
                    relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
                )
                content.append(acquisition_device_type_item)
        if target_regions is not None:
            if not isinstance(target_regions, (list, tuple, set)):
                raise TypeError(
                    'Argument "target_regions" must be a sequence.'
                )
            for target_region in target_regions:
                if not isinstance(target_region, (CodedConcept, Code)):
                    raise TypeError(
                        'Items of argument "target_region" must have type Code or CodedConcept.'
                    )
                target_region_item = CodeContentItem(
                    name=codes.DCM.TargetRegion,
                    value=target_region,
                    relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
                )
                content.append(target_region_item)
        if equivalent_meanings_of_concept_name is not None:
            if not isinstance(equivalent_meanings_of_concept_name, (list, tuple, set)):
                raise TypeError(
                    'Argument "equivalent_meanings_of_concept_name" must be a sequence.'
                )
            for equivalent_meaning_of_concept_name in equivalent_meanings_of_concept_name:
                if not isinstance(equivalent_meaning_of_concept_name, (EquivalentMeaningsOfConceptNameCode, EquivalentMeaningsOfConceptNameText)):
                    raise TypeError(
                        'Items of argument "equivalent_meaning_of_concept_name" must have type EquivalentMeaningsOfConceptNameCode or EquivalentMeaningsOfConceptNameText.'
                    )
                content.extend(equivalent_meaning_of_concept_name)
        if diagnostic_imaging_report_headings is not None:
            if not isinstance(diagnostic_imaging_report_headings, (list, tuple, set)):
                raise TypeError(
                    'Argument "diagnostic_imaging_report_headings" must be a sequence.'
                )
            for diagnostic_imaging_report_heading in diagnostic_imaging_report_headings:
                if not isinstance(diagnostic_imaging_report_heading, DiagnosticImagingReportHeading):
                    raise TypeError(
                        'Items of argument "diagnostic_imaging_report_heading" must have type DiagnosticImagingReportHeading.'
                    )
                content.extend(diagnostic_imaging_report_heading)
        if len(content) > 0:
            item.ContentSequence = content
        self.append(item)
