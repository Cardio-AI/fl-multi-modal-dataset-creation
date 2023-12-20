"""DICOM structured reporting templates."""
import collections
import logging
from copy import deepcopy
from typing import cast, Dict, Iterable, List, Optional, Sequence, Tuple, Union
from enum import Enum
import datetime

from pydicom.dataset import Dataset
from pydicom.sr.coding import Code
from pydicom.sr.codedict import codes
from pydicom.valuerep import DA, DS, TM, DT, PersonName

from highdicom.sr.coding import CodedConcept
from highdicom.sr.content import (
    FindingSite,
    LongitudinalTemporalOffsetFromEvent,
    ImageRegion,
    ImageRegion3D,
    VolumeSurface,
    RealWorldValueMap,
    ReferencedSegment,
    ReferencedSegmentationFrame,
    SourceImageForMeasurementGroup,
    SourceImageForMeasurement,
    SourceImageForSegmentation,
    SourceSeriesForSegmentation
)

from highdicom.sr.enum import (
    GraphicTypeValues,
    GraphicTypeValues3D,
    RelationshipTypeValues,
    ValueTypeValues,
)
from highdicom.uid import UID
from highdicom.sr.utils import (
    find_content_items,
    get_coded_name
)
from highdicom.sr.value_types import (
    CodeContentItem,
    ContainerContentItem,
    ContentItem,
    ContentSequence,
    ImageContentItem,
    NumContentItem,
    PnameContentItem,
    TextContentItem,
    UIDRefContentItem,
    DateTimeContentItem,
    CompositeContentItem
)
from highdicom.sr.template import(
    Template,
    ObservationContext,
    LanguageOfContentItemAndDescendants
)

class ConcernTypes(Enum):

    COMPLAINT = codes.SCT.Complaint
    DISEASE = codes.SCT.Disease
    FINDING = codes.SCT.Finding
    FINDING_REPORTED_BY_PATIENT_INFORMANT = codes.SCT.FindingReportedByPatientInformant
    FUNCTIONAL_PERFORMANCE_AND_ACTIVITY = codes.SCT.FunctionalPerformanceAndActivity
    PROBLEM = codes.SCT.Problem


class CardiacPatientRiskFactors(Enum):
    """CID 3756"""
    HISTORY_OF_CONGESTIVE_HEART_FAILURE = codes.SCT.HistoryOfCongestiveHeartFailure
    HISTORY_OF_DIABETES = codes.SCT.HistoryOfDiabetes
    HISTORY_OF_RENAL_FAILURE = codes.SCT.HistoryOfRenalFailure
    CHRONIC_LUNG_DISEASE = codes.SCT.HistoryOfChronicLungDisease
    HISTORY_OF_CEREBROVASCULAR_DISEASE = codes.SCT.HistoryOfCerebrovascularDisease
    PERIPHERAL_VASCULAR_DISEASE =codes.SCT.PeripheralVascularDisease
    HISTORY_OF_MYOCARDIAL_INFACRTION = codes.SCT.HistoryOfMyocardialInfarction
    HISTORY_OF_HYPERTENSION = codes.SCT.HistoryOfHypertension
    HISTORY_OF_HYPERCHOLESTEROLEMIA = codes.SCT.HistoryOfHypercholesterolemia
    ARRHYTHMIA = Code('44808001', 'SCT', 'Arrhythmia') # codes.SCT.Arrhythmia occurs twice
    HIV_POSITIVE = codes.SCT.HIVPositive
    INFANT_OF_MOTHER_WITH_GESTATIONAL_DIABETES = codes.UMLS.InfantOfMotherWithGestationalDiabetes
    INSULIN_DEPENDENT_MOTHER_IDM = codes.SCT.InsulinDependentMotherIDM


class ProblemStatus(Enum):
    """CID 3770"""
    ACTIVE_PROBLEM =  codes.SCT.ActiveProblem
    CHRONIC = codes.SCT.Chronic
    INTERMITTENT = codes.SCT.Intermittent
    RECURRENT = codes.SCT.Recurrent,
    SUSPECTED = codes.SCT.Suspected
    INACTIVE_PROBLEM = codes.SCT.InactiveProblem
    PROBLEM_RESOLVED = codes.SCT.ProblemResolved
    KNOWN_ABSENT = codes.SCT.KnownAbsent
    WELL_CONTROLLED = codes.SCT.WellControlled


class Severity(Enum):
    """CID 3716"""
    NONE = Code('260413007', 'SCT', 'None')
    MILD = codes.SCT.Mild
    MILD_TO_MODERATE = codes.SCT.MildToModerate
    MODERATE = codes.SCT.Moderate
    MODRATE_TO_SEVERE = codes.SCT.ModerateToSevere
    SEVRE = codes.SCT.Severe
    FATAL = codes.SCT.Fatal


class HealthStatus(Enum):
    """CID 3772"""
    ALIVE = codes.SCT.Alive
    ALIVE_AND_WELL = codes.SCT.AliveAndWell
    IN_REMISSION = codes.SCT.InRemission
    SYMPTOM_FREE = codes.SCT.SymptomFree
    CHRONICALLY_ILL = codes.SCT.ChronicallyIll
    SEVERELY_ILL = codes.SCT.SeverelyIll
    DISABLED = codes.SCT.Disabled
    SEVERELY_DISABLED = codes.SCT.SeverelyDisabled
    DECEASED = codes.SCT.Deceased
    LOST_TO_FOLLOW_UP = codes.SCT.LostToFollowUp


class UseStatus(Enum):
    """CID 3773"""
    ENDED = codes.SCT.Ended
    SUSPENDED = codes.SCT.Suspended
    IN_PROGRESS = codes.SCT.InProgress


class HypertensionTherapy(Enum):
    """CID 3760"""
    BETA_BLOCKER = Code('33252009', 'SCT', 'Beta blocker') # codes.SCT.BetaBlocker two found
    CALCIUM_CHANNEL_BLOCKER = Code('48698004', 'SCT', 'Calcium channel blocker') # codes.SCT.CalciumChannelBlocker two found
    NITRATE_VASODILATOR = codes.SCT.NitrateVasodilator
    ACE_INHIBITOR = codes.SCT.ACEInhibitor
    ANGIOTENSIN_II_RECEPTOR_ANTAGONIST = codes.SCT.AngiotensinIIReceptorAntagonist
    DIURETIC = Code('30492008', 'SCT', 'Diuretic') # codes.SCT.Diuretic two found


class DiabeticTherapy(Enum):
    """CID 3722"""
    DIABETIC_ON_DIETARY_TREATMENT = codes.SCT.DiabeticOnDietaryTreatment
    DIABETIC_ON_ORAL_TEATMENT = codes.SCT.DiabeticOnOralTreatment
    DIABETIC_ON_INSULIN = codes.SCT.DiabeticOnInsulin


class AntilipemicAgents(Enum):
    """CID 3761"""
    ANION_EXCHANGE_RESIN = codes.SCT.AnionExchangeResin
    BILE_ACID_SEQUESTRANT = codes.SCT.BileAcidSequestrant
    FIBRATE = Code('C98150', 'NCIt', 'Fibrate')
    FISH_OILS = codes.SCT.FishOils
    STATINS = codes.SCT.Statins


class AntiarrhythmicAgents(Enum):
    """CID 3762"""
    CLASS_I_ANTIARRHYTHMIC_AGENT = codes.SCT.ClassIAntiarrhythmicAgent
    CLASS_II_ANTIARRHYTHMIC_AGENT = codes.SCT.ClassIIAntiarrhythmicAgent
    CLASS_III_ANTIARRHYTHMIC_AGENT = codes.SCT.ClassIIIAntiarrhythmicAgent
    CLASS_IV_ANTIARRHYTHMIC_AGENT = codes.SCT.ClassIVAntiarrhythmicAgent


class MITypes(Enum):
    """CID 3723"""
    NON_ST_ELEVATION_MYOCARDIAL_INFARTION = codes.SCT.NonSTElevationMyocardialInfarction
    ST_ELEVATION_MYOCARDIAL_INFARTION = codes.SCT.STElevationMyocardialInfarction


class MyocardialInfartionTherapies(Enum):
    """CID 3764"""
    PERCUTANEOUS_CORONARY_INTERVENTION = codes.SCT.PercutaneousCoronaryIntervention
    INSERTION_OF_CORONARY_ARTERY_STENT = codes.SCT.InsertionOfCoronaryArteryStent
    CORONARY_ARTERY_BYPASS_GRAFT = codes.SCT.CoronaryArteryBypassGraft
    THROMBOLYTIC_THERAPY = codes.SCT.ThrombolyticTherapy


class Stages(Enum):
    """CID 3778"""
    STAGE_0 = codes.SCT.Stage0
    STAGE_1 = codes.SCT.Stage1
    STAGE_2 = codes.SCT.Stage2
    STAGE_3 = codes.SCT.Stage3
    STAGE_4 = codes.SCT.Stage4
    STAGE_5 = codes.SCT.Stage5


class SocialHistory(Enum):
    """CID 3774"""
    TOBACCO_SMOKING_BEHAVIOR = codes.SCT.TobaccoSmokingBehavior
    DRUG_MISUSE_BEHAVIOOR = codes.SCT.DrugMisuseBehavior
    EXERCISE = codes.SCT.Exercise
    NUTRITION = codes.SCT.Nutrition
    ALCOHOL_CONSUMPTION = codes.SCT.AlcoholConsumption


class SmokingHistory(Enum):
    """CID 3724"""
    NO_HISTORY_OF_SMOKING = codes.SCT.NoHistoryOfSmoking
    CURRENT_SMOKER = codes.SCT.CurrentSmoker
    FORMER_SMOKER = codes.SCT.FormerSmoker


class DrugMisuseBehavior(Enum):
    """No template but listed here for completion"""
    COCAINE_ABUSE = codes.SCT.CocaineAbuse


class CardiovascularSurgeries(Enum):
    """CID 3721"""
    PERCUTANEOUS_CORONARY_INTERVENTION = codes.SCT.PercutaneousCoronaryIntervention
    CORONARY_ARTERY_BYPASS_GRAFT = codes.SCT.CoronaryArteryBypassGraft
    OPERATION_ON_HEART_VALVE = codes.SCT.OperationOnHeartValve
    ABLATION_OPERATION_FOR_ARRHYTHMIA = codes.SCT.AblationOperationForArrhythmia
    IMPLANTATION_OF_CARDIAC_PACEMAKER = codes.SCT.ImplantationOfCardiacPacemaker
    IMPLANTATION_OF_AUTOMATIC_CARDIAC_DEFIBRILLATOR = codes.SCT.ImplantationOfAutomaticCardiacDefibrillator
    ABDOMINAL_AORTIC_ANEURYSM_STENTING = codes.SCT.AbdominalAorticAneurysmStenting
    HEART_TRANSPLANT = codes.SCT.HeartTransplant
    CORRECTION_OF_CONGENITAL_CARDIOVASCULAR_DEFORMITY = codes.SCT.CorrectionOfCongenitalCardiovascularDeformity


class CardiovascularDiagnosticProcedures(Enum):
    """CID 3757"""
    CARDIAC_BLOOD_POOL_IMAGING_NUCLEAR = codes.SCT.CardiacBloodPoolImagingNuclear
    CARDIAC_CATH_CORONARY_ANGIOGRAM_AND_LEFT_VENTRICULOGRAM = codes.SCT.CardiacCathCoronaryAngiogramAndLeftVentriculogram
    CARDIAC_CATHETERIZATION = codes.SCT.CardiacCatheterization
    CARDIAC_CATHETERIZATION_CORONARY_ANGIOGRAM = codes.SCT.CardiacCatheterizationCoronaryAngiogram
    CARDIAC_CT = codes.SCT.CardiacCT
    CARDIAC_CT_FOR_CALCIUM_SCORING = codes.SCT.CardiacCTForCalciumScoring
    CARDIAC_MRI = codes.SCT.CardiacMRI
    CARDIAC_MRI_STRESS = codes.SCT.CardiacMRIStress
    CT_ANGIOGRAPHY_OF_CORONARY_ARTERIES = codes.SCT.CTAngiographyOfCoronaryArteries
    ECHOCARDIOGRAPHY = codes.SCT.Echocardiography
    EXERCISE_STRESS_ECHOCARDIOGRAPHY = codes.SCT.ExerciseStressEchocardiography
    EXERCISE_TOLERANCE_TEST = codes.SCT.ExerciseToleranceTest
    MAGNETIC_RESONANCE_ANGIOGRAPHY = codes.SCT.MagneticResonanceAngiography
    NUCLEAR_MEDICINE_CARDIOVASCULAR_STUDY = codes.SCT.NuclearMedicineCardiovascularStudy
    PERFUSION_IMAGING_NUCLEAR = codes.SCT.PerfusionImagingNuclear
    PET_HEART_STUDY = codes.SCT.PETHeartStudy
    PHARMACOLOGIC_AND_EXERCISE_STRESS_TEST = codes.SCT.PharmacologicAndExerciseStressTest
    PHARMACOLOGICAL_STRESS_TEST = codes.SCT.PharmacologicalStressTest
    RADIONUCLIDE_ANGIOCARDIOGRAPHY = codes.SCT.RadionuclideAngiocardigraphy
    RADIONUCLIDE_MYOCARDIAL_PERFUSION_STUDY = codes.SCT.RadionuclideMyocardialPerfusionStudy
    SPECT = codes.SCT.SPECT
    STRESS_TEST_USING_CARDIAC_PACING = codes.SCT.StressTestUsingCardiacPacing
    TRANSESOPHAGEAL_ECHOCARDIOGRAPHY = codes.SCT.TransesophagealEchocardiography
    TRANSTHORACIC_ECHOCARDIOGRAPHY = codes.SCT.TransthoracicEchocardiography


class Problem(Template):
    def __init__(
        self,
        concern_type: ConcernTypes,
        problem: Union[Code, CodedConcept],
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        therapy: Optional[Union[Code, CodedConcept]] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        if title is None:
            title = codes.DCM.Concern
        if not isinstance(title, (CodedConcept, Code, )):
            raise TypeError(
                'Argument "title" must have type CodedConcept or Code.'
            )
        item = ContainerContentItem(
            name=title,
            template_id='3829'
        )
        item.ContentSequence = ContentSequence()

        if datetime_concern_noted is not None:
            datetime_concern_noted = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernNoted,
                value=datetime_concern_noted,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            item.ContentSequence.append(datetime_concern_noted)
        
        if datetime_concern_resolved is not None:
            datetime_concern_resolved = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernResolved,
                value=datetime_concern_resolved,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            item.ContentSequence.append(datetime_concern_resolved)
        
        concern_type = CodeContentItem(
            name=concern_type,
            value=problem,
            relationship_type=RelationshipTypeValues.CONTAINS
        )
        item.ContentSequence.append(concern_type)

        if modifier_type is not None and modifier_value is not None:
            mod = CodeContentItem(
                name=modifier_type,
                value=modifier_value,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            item.ContentSequence.append(mod)
        
        if datetime_started is not None:
            datetime_started = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernResolved,
                value=datetime_started,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(datetime_started)
        
        if datetime_problem_resolved is not None:
            datetime_problem_resolved = DateTimeContentItem(
                name=codes.DCM.DatetimeConcernResolved,
                value=datetime_problem_resolved,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(datetime_problem_resolved)
        
        if status is not None:
            status = CodeContentItem(
                name=Code('33999-4', 'LN', 'Status'), # codes.LN.Status
                value=status
            )
            item.ContentSequence.append(status)
        
        if severity is not None:
            severity = CodeContentItem(
                name=codes.SCT.Severity,
                value=severity,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(severity)
        
        if stage is not None:
            stage = CodeContentItem(
                name=codes.SCT.Stage,
                value=stage,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(stage)
        
        if health_status is not None:
            health_status = CodeContentItem(
                name=Code('11323-3', 'LN', 'Health Status'),
                value=health_status,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            item.ContentSequence.append(health_status)
        
        if therapy is not None:
            therapy = CodeContentItem(
                name=codes.SCT.Therapy,
                value=therapy,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            item.ContentSequence.append(therapy)
        
        if use_status is not None:
            use_status = CodeContentItem(
                name=Code('33999-4', 'LN', 'Status'),
                value=use_status,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(use_status)
        
        if comment is not None:
            comment = TextContentItem(
                name=codes.DCM.Comment,
                value=comment,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            item.ContentSequence.append(comment)

        # concern_types = ContainerContentItem(
        #     name=concern_type,
        #     relationship_type=RelationshipTypeValues.CONTAINS
        # )
        # problem_list.ContentSequence = ContentSequence()

        super().__init__([item], is_root=True)


class CardiacPatientRiskFactorsProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        problem: CardiacPatientRiskFactors,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        therapy: Optional[Union[Code, CodedConcept]] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=problem,
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class HistoryOfDiabetesMellitusProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        therapy: DiabeticTherapy,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=codes.SCT.HistoryOfDiabetesMellitus,
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class HistoryOfHypertensionProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        therapy: HypertensionTherapy,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=codes.SCT.HistoryOfHypertension,
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class HistoryOfHypercholesterolemiaProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        therapy: AntilipemicAgents,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=codes.SCT.HistoryOfHypercholesterolemia,
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class ArrhythmiaProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        therapy: AntiarrhythmicAgents,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=Code('44808001', 'SCT', 'Arrhythmia'),
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class HistoryOfMyocardialInfarctionProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        modifier_value: MITypes,
        therapy: MyocardialInfartionTherapies,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        stage: Optional[ProblemStatus] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=codes.SCT.HistoryOfMyocardialInfarction,
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=codes.DCM.TypeOfMyocardialInfarction,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class HistoryOfKidneyDiseaseProblem(Problem):
    def __init__(
        self,
        concern_type: ConcernTypes,
        stage: Stages,
        title: Optional[Union[Code, CodedConcept]] = None,
        # concerns: List[Dict[str, Union[Code, CodedConcept]]],
        datetime_concern_noted: Optional[Union[str, datetime.datetime, DT]] = None,
        datetime_concern_resolved: Optional[Union[str, datetime.datetime, DT]] = None,
        ######### NOT SURE IF HERE OR CHILD CONTAINER
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        datetime_started: Optional[DateTimeContentItem] = None,
        datetime_problem_resolved: Optional[DateTimeContentItem] = None,
        status: Optional[Union[Code, CodedConcept]] = None,
        severity: Optional[Union[Code, CodedConcept]] = None,
        ##########
        health_status: Optional[HealthStatus] = None,
        therapy: Optional[Union[Code, CodedConcept]] = None,
        use_status: Optional[UseStatus] = None, 
        comment: Optional[str] = None # U
    ):
        super().__init__(
            self,
            concern_type=concern_type,
            problem=codes.SCT.HistoryOfKidneyDisease,
            title=title,
            datetime_concern_noted=datetime_concern_noted,
            datetime_concern_resolved=datetime_concern_resolved,
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            datetime_started=datetime_started,
            datetime_problem_resolved=datetime_problem_resolved,
            status=status,
            severity=severity,
            stage=stage,
            health_status=health_status,
            therapy=therapy,
            use_status=use_status, 
            comment=comment
        )


class Procedure(Template):
    """TID 3830"""
    def __init__(
        self,
        procedure_type: Union[Code, CodedConcept],
        procedure: Union[Code, CodedConcept],
        title: Optional[Union[Code, CodedConcept]] = None,
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        procedure_datetime: Optional[Union[str, datetime.datetime, DT]] = None,
        clinical_report: Optional[CompositeContentItem] = None,
        clinical_report_text: Optional[str] = None,
        # document_title: Optional[Union[Code, CodedConcept]] = None,
        service_delivery_location: Optional[str] = None,
        service_performer_person: Optional[Union[str, PersonName]] = None,
        service_performer_organisation: Optional[str] = None,
        comment: Optional[str] = None,
        procedure_result: Optional[Union[Code, CodedConcept]] = None
    ):
        if title is None:
            title = codes.DCM.Concern
        if not isinstance(title, (CodedConcept, Code, )):
            raise TypeError(
                'Argument "title" must have type CodedConcept or Code.'
            )
        item = ContainerContentItem(
            name=title,
            template_id='3830'
        )
        item.ContentSequence = ContentSequence()

        procedure = CodeContentItem(
            name=procedure_type,
            value=procedure,
        )
        item.ContentSequence.append(procedure)

        if all([modifier_type, modifier_value]):
            modifier = CodeContentItem(
                name=modifier_type,
                value=modifier_value,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            item.ContentSequence.append(modifier)
        
        if procedure_datetime is not None:
            procedure_datetime = DateTimeContentItem(
                name=codes.DCM.ProcedureDatetime
                value=procedure_datetime,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(procedure_datetime)

        if clinical_report is not None:
            item.ContentSequence.append(clinical_report)
        
        if clinical_report_text is not None:
            clinical_report_text = TextContentItem(
                name=codes.SCT.ClinicalReport,
                value=clinical_report_text,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(clinical_report_text)
        
        if service_delivery_location is not None:
            service_delivery_location = TextContentItem(
                name=codes.DCM.ServiceDeliveryLocation,
                value=service_delivery_location,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(service_delivery_location)
        
        if all([service_performer_person, service_performer_organisation]):
            raise ValueError('Only person or organisation as service performer')
        
        if service_performer_person is not None:
            service_performer_person = PnameContentItem(
                name=codes.DCM.ServicePerformer,
                value=service_performer_person,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(service_performer_person)
        
        if service_performer_organisation is not None:
            service_performer_organisation = TextContentItem(
                name=codes.DCM.ServicePerformer,
                value=service_performer_organisation,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(service_performer_organisation)
        
        if comment is not None:
            comment = TextContentItem(
                name=codes.DCM.Comment,
                value=comment,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(comment)
        
        if procedure_result is not None:
            procedure_result = CodeContentItem(
                name=codes.DCM.ProcedureResult,
                value=procedure_result,
                relationship_type=RelationshipTypeValues.HAS_PROPERTIES
            )
            item.ContentSequence.append(procedure_result)

        super().__init__([item], is_root=True)


class CardiovascularSurgicalProcedure(Procedure):
    def __init__(
        self,
        # procedure_type: Union[Code, CodedConcept],
        procedure: CardiovascularSurgeries, 
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        procedure_datetime: Optional[Union[str, datetime.datetime, DT]] = None,
        clinical_report: Optional[CompositeContentItem] = None,
        clinical_report_text: Optional[str] = None,
        # document_title: Optional[Union[Code, CodedConcept]] = None,
        service_delivery_location: Optional[str] = None,
        service_performer_person: Optional[Union[str, PersonName]] = None,
        service_performer_organisation: Optional[str] = None,
        comment: Optional[str] = None,
        procedure_result: Optional[Union[Code, CodedConcept]] = None
    ):
        super().__init__(
            self,
            procedure_type=codes.SCT.SurgicalProcedure,
            procedure=procedure, 
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            procedure_datetime=procedure_datetime,
            clinical_report=clinical_report,
            clinical_report_text=clinical_report_text,
            service_delivery_location=service_delivery_location,
            service_performer_person=service_performer_person,
            service_performer_organisation=service_performer_organisation,
            comment=comment,
            procedure_result=procedure_result
        )


class CardiovascularDiagnosticProcedure(Procedure):
    def __init__(
        self,
        # procedure_type: Union[Code, CodedConcept],
        procedure: CardiovascularDiagnosticProcedures, 
        modifier_type: Optional[Union[Code, CodedConcept]] = None,
        modifier_value: Optional[Union[Code, CodedConcept]] = None,
        procedure_datetime: Optional[Union[str, datetime.datetime, DT]] = None,
        clinical_report: Optional[CompositeContentItem] = None,
        clinical_report_text: Optional[str] = None,
        # document_title: Optional[Union[Code, CodedConcept]] = None,
        service_delivery_location: Optional[str] = None,
        service_performer_person: Optional[Union[str, PersonName]] = None,
        service_performer_organisation: Optional[str] = None,
        comment: Optional[str] = None,
        procedure_result: Optional[Union[Code, CodedConcept]] = None
    ):
        super().__init__(
            self,
            procedure_type=codes.SCT.DiagnosticProcedure,
            procedure=procedure, 
            modifier_type=modifier_type,
            modifier_value=modifier_value,
            procedure_datetime=procedure_datetime,
            clinical_report=clinical_report,
            clinical_report_text=clinical_report_text,
            service_delivery_location=service_delivery_location,
            service_performer_person=service_performer_person,
            service_performer_organisation=service_performer_organisation,
            comment=comment,
            procedure_result=procedure_result
        )


cardiovascular_family_history = [
    codes.SCT.FamilyHistoryOfCardiovascularDisease,
    codes.SCT.FamilyHistoryOfDiabetesMellitus,
    codes.SCT.FamilyHistoryOfMyocardialInfarction,
    codes.SCT.FamilyHistoryOfCoronaryArteriosclerosis,
    codes.SCT.NoFamilyHistoryOfDiabetes,
    codes.SCT.NoFamilyHistoryOfCardiovascularDisease,
    codes.SCT.FamilyHistoryUnknown
]

implanted_devices = [
    codes.SCT.CardiacPacemaker,
    codes.SCT.ImplantableDefibrillator,
    codes.SCT.LeftVentricularAssistDevice,
    codes.SCT.InsulinPump
]


class SocialHistoryTextContentItem(TextContentItem):
    def __init__(
        self,
        name: SocialHistory,
        value: str,
        relationship_type: Union[str, RelationshipTypeValues, None] = None
    ):
        super().__init__(
            self,
            name=name,
            value=value,
            relationship_type=relationship_type
        )


class CardiovascularPatientHistory(Template):
    def __init__(
        self,
        title: Optional[Union[Code, CodedConcept]] = None,
        history: Optional[str] = None,
        problem_list: Optional[List[
            CardiacPatientRiskFactorsProblem,
            HistoryOfDiabetesMellitusProblem,
            HistoryOfHypertensionProblem,
            HistoryOfHypercholesterolemiaProblem,
            ArrhythmiaProblem,
            HistoryOfMyocardialInfarctionProblem,
            HistoryOfKidneyDiseaseProblem
        ]] = None,
        social_history: Optional[SocialHistoryTextContentItem] = None,
        tobacco_smoking_behavior: Optional[SmokingHistory] = None,
        drug_misuse_behavior: Optional[DrugMisuseBehavior] = None,
        past_surgical_history: Optional[List[str]] = None,
        past_surgical_procedures: Optional[List[Procedure]] = None,
        diagnostic_history: Optional[List[str]] = None, 
        cardiac_diagnostic_procedures: Optional[List[CardiovascularDiagnosticProcedures]] = None, 
        cholesterol_in_hdl: Optional[float] = None, 
        cholesterol_in_ldl: Optional[float] = None,
        history_of_family_member_diseases = None, # SUBJECT RELATIONSHIP -> M
        history_of_medical_device_use = None
    ):
        
        if title is None:
            title = codes.LN.History
        if not isinstance(title, (CodedConcept, Code, )):
            raise TypeError(
                'Argument "title" must have type CodedConcept or Code.'
            )
        item = ContainerContentItem(
            name=title,
            template_id='3802'
        )
        item.ContentSequence = ContentSequence()

        if history is not None:
            history = TextContentItem(
                name=codes.LN.History,
                value=history,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            item.ContentSequence.append(history)

        if problem_list is not None:
            problem_list = ContainerContentItem(
                name=codes.LN.ProblemList,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            problem_list.ContentSequence = ContentSequence()

            problem_list.ContentSequence.extend(problem_list)

            item.ContentSequence.extent(problem_list)

        if any([social_history, tobacco_smoking_behavior, drug_misuse_behavior]):
            social_history_container = ContainerContentItem(
                name=Code('29762-2', 'LN', 'Social History'),
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            social_history_container.ContentSequence = ContentSequence()
            
            if social_history is not None:
                social_history_container.ContentSequence.append(social_history)

            if tobacco_smoking_behavior is not None:
                tobacco_smoking_behavior = CodeContentItem(
                    name=codes.SCT.TobaccoSmokingBehavior,
                    value=tobacco_smoking_behavior,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                social_history_container.ContentSequence.append(tobacco_smoking_behavior)
            
            if drug_misuse_behavior:
                drug_misuse_behavior = CodeContentItem(
                    name=codes.SCT.DrugMisuseBehavior,
                    value=drug_misuse_behavior,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                social_history_container.ContentSequence.append(drug_misuse_behavior)
            item.ContentSequence.extend(social_history_container)

        if any([past_surgical_history, past_surgical_procedures]):
            past_surgical_history_container = ContainerContentItem(
                name=Code('10167-5', 'LN', 'Past Surgical History'),
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            past_surgical_history_container.ContentSequence = ContentSequence()

            if past_surgical_history:
                for p in past_surgical_history:
                    p = TextContentItem(
                        name=codes.LN.History,
                        value=p,
                        relationship_type=RelationshipTypeValues.CONTAINS
                    )
                    past_surgical_history_container.ContentSequence.append(p)
            
            if past_surgical_procedures is not None:
                # for p in past_surgical_procedures:
                # TODO: CAN I APPEND A INITIATED TEMPLATE?
                past_surgical_history_container.ContentSequence.extend(past_surgical_procedures)
            
            item.ContentSequence.extent(past_surgical_history_container)
        
        if any([diagnostic_history, cardiac_diagnostic_procedures, cholesterol_in_hdl, cholesterol_in_ldl]):
            diagnostic_container = ContainerContentItem(
                name=codes.LN.RelevantDiagnosticTestsAndOrLaboratoryData,
                relationship_type=RelationshipTypeValues.CONTAINS
            )
            diagnostic_container.ContentSequence = ContentSequence()

            if diagnostic_history is not None:
                for h in diagnostic_history:
                    h = TextContentItem(
                        name=codes.LN.History,
                        value=h,
                        relationship_type=RelationshipTypeValues.CONTAINS
                    )
                    diagnostic_container.ContentSequence.append(h)
            
            if cardiac_diagnostic_procedures is not None:
                diagnostic_container.ContentSequence.extend(cardiac_diagnostic_procedures)
            
            if cholesterol_in_hdl is not None:
                cholesterol_in_hdl = NumContentItem(
                    name=Code('2086-7', 'LN', 'Cholesterol.in HDL'),
                    value=cholesterol_in_hdl,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                diagnostic_container.ContentSequence.append(cholesterol_in_hdl)
            
            if cholesterol_in_ldl is not None:
                cholesterol_in_ldl = NumContentItem(
                    name=Code('2089-1', 'LN', 'Cholesterol.in LDL'),
                    value=cholesterol_in_ldl,
                    relationship_type=RelationshipTypeValues.CONTAINS
                )
                diagnostic_container.ContentSequence.append(cholesterol_in_ldl)
            
            item.ContentSequence.extend(diagnostic_container)
        
        # HISTORY OF MEDICATION USE

        super.__init__([item], is_root=True)

class PatientCharacteristicsForECG(Template):
    def __init__(
        self,
        subject_age: Optional[str] = None,
        subject_sex: Optional[str] = None,
        patient_height: Optional[str] = None,
        patient_weight: Optional[str] = None,
        systolic_blood_pressure: Optional[str] = None,
        diastolic_blood_pressure: Optional[str] = None,
        patient_state: Optional[str] = None,
        pacemaker_in_situ: Optional[str] = None,
        icd_in_situ: Optional[str] = None,
    ):
        super().__init__()
        pass
    pass

class PriorECGExam(Template):
    def __init__(
        self,
        prior_procedure_descriptions,
        comparison_with_prior_exam_done,
        procedure_datetime,
        procedure_stdy_instance_uid,
        prior_report_for_current_patient,
        source_of_measurement
    ):
        super().__init__()

class ECGWaveFormInformation(Template):
    pass

class QuantitativeAnalysis:
    pass

class ECGGlobalMeasurements(Template):
    pass

class ECGLeadMeasurements(Template):
    pass

class ECGQualitativeAnalysis(Template):
    pass

class SummaryECG(Template):
    pass

class ECGReport(Template):

    """:dcm:`TID 1500 <part16/chapter_A.html#sect_TID_1500>`
    Measurement Report
    """

    def __init__(
        self,
        observation_context: ObservationContext,
        procedure_reported: Union[
            Union[CodedConcept, Code],
            Sequence[Union[CodedConcept, Code]],
        ],
        # imaging_measurements: Optional[
        #     Sequence[
        #         Union[
        #             PlanarROIMeasurementsAndQualitativeEvaluations,
        #             VolumetricROIMeasurementsAndQualitativeEvaluations,
        #             MeasurementsAndQualitativeEvaluations,
        #         ]
        #     ]
        # ] = None,
        title: Optional[Union[CodedConcept, Code]] = None,
        language_of_content_item_and_descendants: Optional[
            LanguageOfContentItemAndDescendants
        ] = None,
        indications_for_procedure = None,
        finding = None,
        cardiovascular_patient_history = None,
        patient_characteristics_for_ecg = None,
        prior_ecg_exam = None,
        ecg_waveform_information = None,
        quantitative_analysis = None,
        ecg_global_measurements = None,
        ecg_lead_measurements = None,
        ecg_qualitative_analysis = None,
        summary_ecg = None
        # referenced_images: Optional[
        #     Sequence[Dataset]
        # ] = None
    ):
        """

        Parameters
        ----------
        observation_context: highdicom.sr.ObservationContext
            description of the observation context
        procedure_reported: Union[Union[highdicom.sr.CodedConcept, pydicom.sr.coding.Code], Sequence[Union[highdicom.sr.CodedConcept, pydicom.sr.coding.Code]]]
            one or more coded description(s) of the procedure (see
            :dcm:`CID 100 <part16/sect_CID_100.html>`
            "Quantitative Diagnostic Imaging Procedures" for options)
        imaging_measurements: Union[Sequence[Union[highdicom.sr.PlanarROIMeasurementsAndQualitativeEvaluations, highdicom.sr.VolumetricROIMeasurementsAndQualitativeEvaluations, highdicom.sr.MeasurementsAndQualitativeEvaluations]]], optional
            measurements and qualitative evaluations of images or regions
            within images
        title: Union[highdicom.sr.CodedConcept, pydicom.sr.coding.Code, None], optional
            title of the report (see :dcm:`CID 7021 <part16/sect_CID_7021.html>`
            "Measurement Report Document Titles" for options)
        language_of_content_item_and_descendants: Union[highdicom.sr.LanguageOfContentItemAndDescendants, None], optional
            specification of the language of report content items
            (defaults to English)
        referenced_images: Union[Sequence[pydicom.Dataset], None], optional
            Images that should be included in the library

        """  # noqa: E501
        if title is None:
            title = codes.cid7021.ImagingMeasurementReport
        if not isinstance(title, (CodedConcept, Code, )):
            raise TypeError(
                'Argument "title" must have type CodedConcept or Code.'
            )
        item = ContainerContentItem(
            name=title,
            template_id='1500'
        )
        item.ContentSequence = ContentSequence()
        if language_of_content_item_and_descendants is None:
            language_of_content_item_and_descendants = \
                LanguageOfContentItemAndDescendants(DEFAULT_LANGUAGE)
        item.ContentSequence.extend(
            language_of_content_item_and_descendants
        )
        item.ContentSequence.extend(observation_context)
        if isinstance(procedure_reported, (CodedConcept, Code, )):
            procedure_reported = [procedure_reported]
        for procedure in procedure_reported:
            procedure_item = CodeContentItem(
                name=codes.DCM.ProcedureReported,
                value=procedure,
                relationship_type=RelationshipTypeValues.HAS_CONCEPT_MOD
            )
            item.ContentSequence.append(procedure_item)
        # if referenced_images:
        #     image_library = ImageLibrary(referenced_images)
        #     item.ContentSequence.extend(image_library)

        # measurements: Union[
        #     MeasurementsAndQualitativeEvaluations,
        #     PlanarROIMeasurementsAndQualitativeEvaluations,
        #     VolumetricROIMeasurementsAndQualitativeEvaluations,
        # ]
        # if imaging_measurements is not None:
        #     measurement_types = (
        #         PlanarROIMeasurementsAndQualitativeEvaluations,
        #         VolumetricROIMeasurementsAndQualitativeEvaluations,
        #         MeasurementsAndQualitativeEvaluations,
        #     )
        #     container_item = ContainerContentItem(
        #         name=codes.DCM.ImagingMeasurements,
        #         relationship_type=RelationshipTypeValues.CONTAINS
        #     )
        #     container_item.ContentSequence = ContentSequence()
        #     for measurements in imaging_measurements:
        #         if not isinstance(measurements, measurement_types):
        #             raise TypeError(
        #                 'Measurements must have one of the following types: '
        #                 '"{}"'.format(
        #                     '", "'.join(
        #                         [
        #                             t.__name__
        #                             for t in measurement_types
        #                         ]
        #                     )
        #                 )
        #             )
        #         container_item.ContentSequence.extend(measurements)
        item.ContentSequence.append(container_item)
        super().__init__([item], is_root=True)
