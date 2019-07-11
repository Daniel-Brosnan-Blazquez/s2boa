"""
Automated tests for the ingestion of the REP_ARC files

Written by DEIMOS Space S.L. (dibb)

module ingestions
"""
# Import python utilities
import os
import sys
import unittest
import datetime
from dateutil import parser

# Import engine of the DDBB
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine
from eboa.engine.query import Query
from eboa.datamodel.base import Session, engine, Base
from eboa.engine.errors import LinksInconsistency, UndefinedEventLink, DuplicatedEventLinkRef, WrongPeriod, SourceAlreadyIngested, WrongValue, OddNumberOfCoordinates, EboaResourcesPathNotAvailable, WrongGeometry, ErrorParsingDictionary
from eboa.engine.query import Query

# Import datamodel
from eboa.datamodel.dim_signatures import DimSignature
from eboa.datamodel.events import Event, EventLink, EventKey, EventText, EventDouble, EventObject, EventGeometry, EventBoolean, EventTimestamp
from eboa.datamodel.gauges import Gauge
from eboa.datamodel.sources import Source, SourceStatus
from eboa.datamodel.explicit_refs import ExplicitRef, ExplicitRefGrp, ExplicitRefLink
from eboa.datamodel.annotations import Annotation, AnnotationCnf, AnnotationText, AnnotationDouble, AnnotationObject, AnnotationGeometry, AnnotationBoolean, AnnotationTimestamp

# Import ingestion
import eboa.ingestion.eboa_ingestion as ingestion

class TestEngine(unittest.TestCase):
    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Create session to connectx to the database
        self.session = Session()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

    def tearDown(self):
        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()
        self.session.close()
        
    def test_rep_arc_L0_only(self):

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 2

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29   ", "op": "=="}],
                                                 validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                                  generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                                 processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                                 names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        #Check datatake
        datatake = self.query_eboa.get_annotations(explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"},
                                                   annotation_cnf_names = {"op": "like", "filter": "DATATAKE"})

        assert len(datatake) == 1

        #Check baseline
        baseline = self.query_eboa.get_annotations(explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"},
                                                   annotation_cnf_names = {"op": "like", "filter": "BASELINE"})

        assert len(baseline) == 1

        #Check definite footprint
        definite_footprint = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "FOOTPRINT"},
                                                     explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085229_D01_N02.06"})

        assert definite_footprint[0].get_structured_values() == [{
            'type': 'object',
            'name': 'details',
            'values': [{'type': 'geometry',
                'name': 'footprint',
                'value': 'POLYGON ((27.5923694065675 28.6897912912051, 27.8617502445779 28.6464983273278, 27.7690524083984 28.2803979779816, 27.4991925556512 28.322475522552, 27.5923694065675 28.6897912912051))'
                }]
        }]


        # Check definite_data_size
        definite_data_size = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "SIZE"},
                                                             explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085324_D10_N02.06"})
                                                             #value_filters= [{"name": {"str": "size", "op": "like"}, "type": "double", "value": {"op": "like", "value": "18371751"}}])

        assert definite_data_size[0].get_structured_values() == [{
            'type': 'object',
            'name': 'details',
            'values': [{
                "value": "18371751.0",
                "type": "double",
                "name": "size"
                    }]
        }]

        # Check definite_cloud_percentage
        definite_cloud_percentage = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "CLOUD_PERCENTAGE"},
                                                                    explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085334_D10_N02.06"})
                                                                    #value_filters= [{"name": {"str": "cloud_percentage", "op": "like"}, "type": "double", "value": {"op": "like", "value": "0"}}])

        assert definite_cloud_percentage[0].get_structured_values() == [{
            'type': 'object',
            'name': 'details',
            'values': [{
                "value": "0.0",
                "type": "double",
                "name": "cloud_percentage"
                    }]
        }]

        # Check definite_physical_url
        definite_physical_url = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "PHYSICAL_URL"},
                                                                explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085338_D10_N02.06"})
                                                                #value_filters= [{"name": {"str": "physical_url", "op": "like"}, "type": "string", "value": {"op": "like", "value": "https://pac1dag.sentinel2.eo.esa.int/restsrv/rest/download?PdiID=S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085338_D10_N02.06&dsPdiID=S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"}}])

        assert definite_physical_url[0].get_structured_values() == [{
            'type': 'object',
            'name': 'details',
            'values': [{
                "value": "https://pac1dag.sentinel2.eo.esa.int/restsrv/rest/download?PdiID=S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085338_D10_N02.06&dsPdiID=S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06",
                "type": "text",
                "name": "physical_url"
                    }]
        }]

        # Check definite_indexing_time
        definite_indexing_time = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "INDEXING_TIME"},
                                                                 explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085302_D01_N02.06"})
                                                                 #value_filters= [{"name": {"str": "indexing_time", "op": "like"}, "type": "timestamp", "value": {"op": "like", "value": "2018-07-21T11:01:40"}}])

        assert definite_indexing_time[0].get_structured_values() == [{
            'type': 'object',
            'name': 'details',
            'values': [{
                "value": "2018-07-21T11:01:40",
                "type": "timestamp",
                "name": "indexing_time"
                    }]
        }]

        #Check footprints
        footprints = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "FOOTPRINT"})

        assert len(footprints) == 361

        # Check data sizes
        data_sizes = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "SIZE"})

        assert len(data_sizes) == 361

        # Check cloud percentages
        cloud_percentages = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "CLOUD_PERCENTAGE"})

        assert len(cloud_percentages) == 361

        # Check physical urls
        physical_urls = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "PHYSICAL_URL"})

        assert len(physical_urls) == 361

        # Check indexing times
        indexing_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "INDEXING_TIME"})

        assert len(indexing_times) == 361

        # Check datastrip_sensing_explicit_ref
        datastrip_sensing_er = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                                 groups =  {"op": "like", "filter": "L0_DS"})

        assert len(datastrip_sensing_er) == 1

        # Check datastrip_sensing_explicit_ref
        granule_er = self.query_eboa.get_explicit_refs(groups = {"op": "like", "filter": "L0_GR"})

        assert len(granule_er) == 360

        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"},
                                                 gauge_names = {"op": "like", "filter": "PROCESSING_VALIDITY"})

        assert len(processing_validities) == 1

    def test_rep_arc_L0_plan(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        # Check sources
        # L0
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-16 11:41:50", "op": "=="}],
                                             processors = {"filter": "planning_processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]
        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date":  "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1

        processing_validity_l0 = processing_validities[0]

        # Check links with PROCESSING VALIDITY
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1

        assert processing_validity_l0.get_structured_values() == [{
            "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L0",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "type": "text",
                    "name": "processing_centre"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text",
                    "name": "matching_plan_status"
                },
                {
                    "value": "NO_MATCHED_ISP_VALIDITY",
                    "type": "text",
                    "name": "matching_reception_status"
                },
                {
                    "value": "16077.0",
                    "type": "double",
                    "name": "sensing_orbit"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "type": "object",
            "name": "details"
        }]

        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l0 = planning_completeness[0]

        assert planning_completeness_l0.get_structured_values() == [{
            "name": "details",
            "values": [
                {
                    "name": "status",
                    "value": "COMPLETE",
                    "type": "text"
                },
                {
                    "name": "level",
                    "value": "L0",
                    "type": "text"
                },
                {
                    "name": "satellite",
                    "value": "S2A",
                    "type": "text"
                },
                {
                    "name": "processing_centre",
                    "value": "EPA_",
                    "type": "text"
                },
                {
                    "name": "matching_plan_status",
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text"
                },
                {
                    "name": "matching_reception_status",
                    "value": "NO_MATCHED_ISP_VALIDITY",
                    "type": "text"
                },
                {
                    "name": "sensing_orbit",
                    "value": "16077.0",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "type": "object"
        }]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

    def test_rep_arc_L0_with_rep_pass(self):

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:35.993268", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:55", "op": "=="}],
                                             processors = {"filter": "processing_received_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        isp_validity = self.query_eboa.get_events(gauge_names = {"filter": "ISP_VALIDITY", "op": "like"})[0]

        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l0 = processing_validities[0]

        # Check links with PROCESSING VALIDITY
        link_to_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_isp_validity) == 1

        link_from_isp_validity = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "ISP_VALIDITY", "op": "like"})

        assert len(link_from_isp_validity) == 1

        assert processing_validity_l0.get_structured_values() == [{
           "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L0",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "type": "text",
                    "name": "processing_centre"
                },
                {
                    "value": "NO_MATCHED_PLANNED_IMAGING",
                    "type": "text",
                    "name": "matching_plan_status"
                },
                {
                    "value": "MATCHED_ISP_VALIDITY",
                    "type": "text",
                    "name": "matching_reception_status"
                },
                {
                    "value": "16078.0",
                    "type": "double",
                    "name": "downlink_orbit"
                }
            ],
            "type": "object",
            "name": "details"
        }]

    def test_rep_arc_L0_dpc(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources(names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(processors = {"filter": ["planning_processing_ingestion_rep_arc.py", "processing_ingestion_rep_arc.py"], "op": "in"},
                                                 names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 0

    def test_rep_arc_L1C_only(self):

        filename = "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29.000000", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:11:24", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        processing_validities = self.query_eboa.get_events(explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"},
                                                 gauge_names = {"op": "like", "filter": "PROCESSING_VALIDITY"})

        assert len(processing_validities) == 0

    def test_rep_arc_L1C_with_L0(self):

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29   ", "op": "=="}],
                                                 validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                                  generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                                 processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                                 names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        #L1C
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                         validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                          generation_time_filters = [{"date": "2018-07-21T11:11:24", "op": "=="}],
                                         processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                         names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        processing_validities = self.query_eboa.get_events(explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"},
                                                 gauge_names = {"op": "like", "filter": "PROCESSING_VALIDITY"})

        assert len(processing_validities) == 1

        processing_validity_l1c = processing_validities[0]

        assert processing_validity_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "name": "processing_centre",
                    "type": "text"
                },
                {
                    "value": "NO_MATCHED_PLANNED_IMAGING",
                    "name": "matching_plan_status",
                    "type": "text"
                },
                {
                    "value": "NO_MATCHED_ISP_VALIDITY",
                    "name": "matching_reception_status",
                    "type": "text"
                }
            ],
            "name": "details",
            "type": "object"
        }]

        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1c = planning_completeness[0]

        assert planning_completeness_l1c.get_structured_values() == [{
            "name": "details",
            "values": [
                {
                    "name": "status",
                    "value": "COMPLETE",
                    "type": "text"
                },
                {
                    "name": "level",
                    "value": "L1C",
                    "type": "text"
                },
                {
                    "name": "satellite",
                    "value": "S2A",
                    "type": "text"
                },
                {
                    "name": "processing_centre",
                    "value": "EPA_",
                    "type": "text"
                },
                {
                    "name": "matching_plan_status",
                    "value": "NO_MATCHED_PLANNED_IMAGING",
                    "type": "text"
                },
                {
                    "name": "matching_reception_status",
                    "value": "NO_MATCHED_ISP_VALIDITY",
                    "type": "text"
                }
            ],
            "type": "object"
        }]

    def test_rep_arc_L1C_with_L0_plan(self):
        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        #L0
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        #L1C
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                         validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                          generation_time_filters = [{"date": "2018-07-21T11:11:24", "op": "=="}],
                                         processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                         names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"},
                                                 gauge_names = {"op": "like", "filter": "PROCESSING_VALIDITY"})

        assert len(processing_validities) == 1

        processing_validity_l1c = processing_validities[0]

        # Check links with PROCESSING VALIDITY
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1

        assert processing_validity_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "name": "processing_centre",
                    "type": "text"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "name": "matching_plan_status",
                    "type": "text"
                },
                {
                    "value": "NO_MATCHED_ISP_VALIDITY",
                    "name": "matching_reception_status",
                    "type": "text"
                },
                {
                    "value": "16077.0",
                    "name": "sensing_orbit",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]

        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1c = planning_completeness[0]

        assert planning_completeness_l1c.get_structured_values() == [{
            "name": "details",
            "values": [
                {
                    "name": "status",
                    "value": "COMPLETE",
                    "type": "text"
                },
                {
                    "name": "level",
                    "value": "L1C",
                    "type": "text"
                },
                {
                    "name": "satellite",
                    "value": "S2A",
                    "type": "text"
                },
                {
                    "name": "processing_centre",
                    "value": "EPA_",
                    "type": "text"
                },
                {
                    "name": "matching_plan_status",
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text"
                },
                {
                    "name": "matching_reception_status",
                    "value": "NO_MATCHED_ISP_VALIDITY",
                    "type": "text"
                },
                {
                    "name": "sensing_orbit",
                    "value": "16077.0",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "type": "object"
        }]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

    def test_rep_arc_L1C_with_L0_plan_rep_pass(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-16 11:41:50", "op": "=="}],
                                             processors = {"filter": "planning_processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:11:24", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-16 11:41:50", "op": "=="}],
                                             processors = {"filter": "planning_processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]
        isp_validity = self.query_eboa.get_events(gauge_names = {"filter": "ISP_VALIDITY", "op": "like"})[0]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1c = processing_validities[0]

        # Check links with PROCESSING VALIDITY
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1

        # Check links with PROCESSING VALIDITY
        link_to_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_isp_validity) == 1

        link_from_isp_validity = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "ISP_VALIDITY", "op": "like"})

        assert len(link_from_isp_validity) == 1

        assert processing_validity_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "name": "processing_centre",
                    "type": "text"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "name": "matching_plan_status",
                    "type": "text"
                },
                {
                    "value": "MATCHED_ISP_VALIDITY",
                    "name": "matching_reception_status",
                    "type": "text"
                },
                {
                    "value": "16077.0",
                    "name": "sensing_orbit",
                    "type": "double"
                },
                {
                    "value": "16078.0",
                    "name": "downlink_orbit",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]

    def test_rep_arc_L0_L1B_L1C_with_plan_and_rep_pass(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T115133_L1B.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-16 11:41:50", "op": "=="}],
                                             processors = {"filter": "planning_processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:01:40", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:56", "op": "=="}],
                                             processors = {"filter": "processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:35.993268", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:55", "op": "=="}],
                                             processors = {"filter": "processing_received_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T110140_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1B
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:51:33", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T115133_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:56", "op": "=="}],
                                             processors = {"filter": "processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T115133_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:35.993268", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:55", "op": "=="}],
                                             processors = {"filter": "processing_received_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T115133_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-16 11:41:50", "op": "=="}],
                                             processors = {"filter": "planning_processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T115133_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:11:24", "op": "=="}],
                                             processors = {"filter": "ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14.000618", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:56", "op": "=="}],
                                             processors = {"filter": "processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-16 11:41:50", "op": "=="}],
                                             processors = {"filter": "planning_processing_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T08:52:35.993268", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:12.226646", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:40:55", "op": "=="}],
                                             processors = {"filter": "processing_received_ingestion_rep_arc.py", "op": "like"},
                                             names = {"filter": "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]
        isp_validity = self.query_eboa.get_events(gauge_names = {"filter": "ISP_VALIDITY", "op": "like"})[0]

        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l0 = processing_validities[0]

        # Check links with PROCESSING VALIDITY
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(imaging_plan.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1

        link_to_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_isp_validity) == 1

        link_from_isp_validity = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "ISP_VALIDITY", "op": "like"})

        assert len(link_from_isp_validity) == 1

        assert processing_validity_l0.get_structured_values() == [{
            "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L0",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "type": "text",
                    "name": "processing_centre"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text",
                    "name": "matching_plan_status"
                },
                {
                    "value": "MATCHED_ISP_VALIDITY",
                    "type": "text",
                    "name": "matching_reception_status"
                },
                {
                    "value": "16077.0",
                    "type": "double",
                    "name": "sensing_orbit"
                },
                {
                    "value": "16078.0",
                    "type": "double",
                    "name": "downlink_orbit"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "type": "object",
            "name": "details"
        }]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1b = processing_validities[0]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1c = processing_validities[0]

        assert processing_validity_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "COMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "name": "processing_centre",
                    "type": "text"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "name": "matching_plan_status",
                    "type": "text"
                },
                {
                    "value": "MATCHED_ISP_VALIDITY",
                    "name": "matching_reception_status",
                    "type": "text"
                },
                {
                    "value": "16077.0",
                    "name": "sensing_orbit",
                    "type": "double"
                },
                {
                    "value": "16078.0",
                    "name": "downlink_orbit",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.419269 27.857385, 30.35928 27.640617, 30.299475 27.423826, 30.239869 27.20701, 30.180461 26.99017, 30.121243 26.773307, 30.062203 26.556421, 30.003354 26.339511, 29.944694 26.122579, 29.886209 25.905624, 29.8279 25.688646, 29.769772 25.471647, 29.711823 25.254626, 29.654037 25.037583, 29.596423 24.820519, 29.538981 24.603434, 29.481708 24.386328, 29.424589 24.169201, 29.367637 23.952054, 29.310849 23.734887, 29.254217 23.5177, 29.197736 23.300493, 29.141414 23.083266, 29.085248 22.86602, 29.029226 22.648756, 28.973353 22.431472, 28.91763 22.21417, 28.862056 21.996849, 28.806615 21.779511, 26.083441 22.359271, 26.134722 22.576988, 26.18607 22.794693, 26.237519 23.012385, 26.289072 23.230065, 26.340721 23.44773, 26.39245 23.665384, 26.444288 23.883024, 26.496237 24.10065, 26.548277 24.318263, 26.600413 24.535863, 26.652665 24.753448, 26.705034 24.971019, 26.757489 25.188576, 26.810058 25.406119, 26.862749 25.623646, 26.915559 25.841159, 26.968461 26.058658, 27.02149 26.276141, 27.074648 26.493608, 27.127919 26.711061, 27.181301 26.928498, 27.234817 27.145919, 27.28847 27.363323, 27.342231 27.580712, 27.396121 27.798085, 27.450154 28.015441, 27.50433 28.23278, 27.558611 28.450103, 30.419269 27.857385))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]

        # Check ISP validity completeness
        isp_completeness = self.query_eboa.get_events(gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                      value_filters = [{"name": {"str": "status", "op": "like"}, "type": "text", "value": {"op": "like", "value": "MISSING"}}])

        assert len(isp_completeness) == 0

        isp_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(isp_completeness) == 1
        isp_completeness_l0 = isp_completeness[0]

        isp_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(isp_completeness) == 1
        isp_completeness_l1b = isp_completeness[0]

        isp_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(isp_completeness) == 1
        isp_completeness_l1c = isp_completeness[0]

        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l0 = planning_completeness[0]

        assert planning_completeness_l0.get_structured_values() == [{
            "name": "details",
            "values": [
                {
                    "name": "status",
                    "value": "COMPLETE",
                    "type": "text"
                },
                {
                    "name": "level",
                    "value": "L0",
                    "type": "text"
                },
                {
                    "name": "satellite",
                    "value": "S2A",
                    "type": "text"
                },
                {
                    "name": "processing_centre",
                    "value": "EPA_",
                    "type": "text"
                },
                {
                    "name": "matching_plan_status",
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text"
                },
                {
                    "name": "matching_reception_status",
                    "value": "MATCHED_ISP_VALIDITY",
                    "type": "text"
                },
                {
                    "name": "sensing_orbit",
                    "value": "16077.0",
                    "type": "double"
                },
                {
                    "name": "downlink_orbit",
                    "value": "16078.0",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "type": "object"
        }]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1b = planning_completeness[0]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1c = planning_completeness[0]

        assert planning_completeness_l1c.get_structured_values() == [{
            "name": "details",
            "values": [
                {
                    "name": "status",
                    "value": "COMPLETE",
                    "type": "text"
                },
                {
                    "name": "level",
                    "value": "L1C",
                    "type": "text"
                },
                {
                    "name": "satellite",
                    "value": "S2A",
                    "type": "text"
                },
                {
                    "name": "processing_centre",
                    "value": "EPA_",
                    "type": "text"
                },
                {
                    "name": "matching_plan_status",
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text"
                },
                {
                    "name": "matching_reception_status",
                    "value": "MATCHED_ISP_VALIDITY",
                    "type": "text"
                },
                {
                    "name": "sensing_orbit",
                    "value": "16077.0",
                    "type": "double"
                },
                {
                    "name": "downlink_orbit",
                    "value": "16078.0",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.419269 27.857385, 30.35928 27.640617, 30.299475 27.423826, 30.239869 27.20701, 30.180461 26.99017, 30.121243 26.773307, 30.062203 26.556421, 30.003354 26.339511, 29.944694 26.122579, 29.886209 25.905624, 29.8279 25.688646, 29.769772 25.471647, 29.711823 25.254626, 29.654037 25.037583, 29.596423 24.820519, 29.538981 24.603434, 29.481708 24.386328, 29.424589 24.169201, 29.367637 23.952054, 29.310849 23.734887, 29.254217 23.5177, 29.197736 23.300493, 29.141414 23.083266, 29.085248 22.86602, 29.029226 22.648756, 28.973353 22.431472, 28.91763 22.21417, 28.862056 21.996849, 28.806615 21.779511, 26.083441 22.359271, 26.134722 22.576988, 26.18607 22.794693, 26.237519 23.012385, 26.289072 23.230065, 26.340721 23.44773, 26.39245 23.665384, 26.444288 23.883024, 26.496237 24.10065, 26.548277 24.318263, 26.600413 24.535863, 26.652665 24.753448, 26.705034 24.971019, 26.757489 25.188576, 26.810058 25.406119, 26.862749 25.623646, 26.915559 25.841159, 26.968461 26.058658, 27.02149 26.276141, 27.074648 26.493608, 27.127919 26.711061, 27.181301 26.928498, 27.234817 27.145919, 27.28847 27.363323, 27.342231 27.580712, 27.396121 27.798085, 27.450154 28.015441, 27.50433 28.23278, 27.558611 28.450103, 30.419269 27.857385))"
                        }
                    ]
                }
            ],
            "type": "object"
        }]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:02.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:56.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

    def test_rep_arc_gaps_L1C_with_L0_plan_rep_pass(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_REP_PASS_WITH_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_L0_WITH_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_ARC____EPA__20180721T111124_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l0 = processing_validities[0]

        assert processing_validity_l0.get_structured_values() == [{
            "values": [
                {
                    "value": "INCOMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L0",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "type": "text",
                    "name": "processing_centre"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "type": "text",
                    "name": "matching_plan_status"
                },
                {
                    "value": "MATCHED_ISP_VALIDITY",
                    "type": "text",
                    "name": "matching_reception_status"
                },
                {
                    "value": "16077.0",
                    "type": "double",
                    "name": "sensing_orbit"
                },
                {
                    "value": "16078.0",
                    "type": "double",
                    "name": "downlink_orbit"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "type": "object",
            "name": "details"
        }]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1c = processing_validities[0]

        assert processing_validity_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "INCOMPLETE",
                    "name": "status",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "value": "EPA_",
                    "name": "processing_centre",
                    "type": "text"
                },
                {
                    "value": "MATCHED_PLANNED_IMAGING",
                    "name": "matching_plan_status",
                    "type": "text"
                },
                {
                    "value": "MATCHED_ISP_VALIDITY",
                    "name": "matching_reception_status",
                    "type": "text"
                },
                {
                    "value": "16077.0",
                    "name": "sensing_orbit",
                    "type": "double"
                },
                {
                    "value": "16078.0",
                    "name": "downlink_orbit",
                    "type": "double"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.451975 27.975229, 30.39206 27.759176, 30.332348 27.543099, 30.272837 27.326998, 30.213507 27.110873, 30.154369 26.894725, 30.095424 26.678554, 30.036668 26.462359, 29.978082 26.246142, 29.919683 26.029902, 29.861468 25.813639, 29.803427 25.597355, 29.745555 25.381049, 29.687861 25.164721, 29.630341 24.948372, 29.572981 24.732001, 29.515789 24.51561, 29.458764 24.299199, 29.401906 24.082766, 29.345197 23.866314, 29.28865 23.649842, 29.232265 23.43335, 29.176031 23.216838, 29.119946 23.000307, 29.064015 22.783757, 29.008237 22.567189, 28.952599 22.350601, 28.897107 22.133996, 28.841762 21.917372, 28.786561 21.70073, 28.731492 21.48407, 26.013899 22.063325, 26.064892 22.280354, 26.115951 22.497372, 26.167107 22.714377, 26.218365 22.931369, 26.269716 23.148348, 26.321145 23.365315, 26.37268 23.582269, 26.424322 23.799209, 26.476052 24.016137, 26.527877 24.233051, 26.579815 24.449952, 26.631868 24.666838, 26.684 24.883711, 26.736247 25.10057, 26.788613 25.317414, 26.84109 25.534243, 26.89366 25.751059, 26.946354 25.967859, 26.999175 26.184644, 27.0521 26.401415, 27.105138 26.618171, 27.158307 26.83491, 27.21161 27.051634, 27.26501 27.268343, 27.318543 27.485036, 27.372216 27.701711, 27.426019 27.918371, 27.479933 28.135015, 27.533991 28.351642, 27.588197 28.568252, 30.451975 27.975229))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:35", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:52:37.209040", "op": "=="}])

        assert len(processing_gaps) == 1
        first_processing_gap_l0 = processing_gaps[0]

        # Check links with PROCESSING VALIDITY
        link_to_gap = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(first_processing_gap_l0.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_gap) == 1

        link_from_gap = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(first_processing_gap_l0.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert len(link_from_gap) == 1

        assert first_processing_gap_l0.get_structured_values() == [{
            "values": [
                {
                    "value": "12.0",
                    "name": "detector",
                    "type": "double"
                },
                {
                    "value": "reception",
                    "name": "source",
                    "type": "text"
                },
                {
                    "value": "L0",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.318115 27.49149, 27.467039 28.083276, 27.467039 28.083276, 30.318115 27.49149))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:37.209040", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:52:40", "op": "=="}])

        assert len(processing_gaps) == 1
        second_processing_gap_l0 = processing_gaps[0]

        # Check links with PROCESSING VALIDITY
        link_to_gap = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(second_processing_gap_l0.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_gap) == 1

        link_from_gap = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(second_processing_gap_l0.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert len(link_from_gap) == 1

        assert second_processing_gap_l0.get_structured_values() == [{
            "values": [
                {
                    "value": "12.0",
                    "name": "detector",
                    "type": "double"
                },
                {
                    "value": "processing",
                    "name": "source",
                    "type": "text"
                },
                {
                    "value": "L0",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.272837 27.326998, 27.426019 27.918371, 27.426019 27.918371, 30.272837 27.326998))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]


        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:35", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:52:37.209040", "op": "=="}])

        assert len(processing_gaps) == 1
        first_processing_gap_l1c = processing_gaps[0]

        # Check links with PROCESSING VALIDITY
        link_to_gap = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(first_processing_gap_l1c.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_gap) == 1

        link_from_gap = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(first_processing_gap_l1c.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert len(link_from_gap) == 1

        assert first_processing_gap_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "12.0",
                    "name": "detector",
                    "type": "double"
                },
                {
                    "value": "reception",
                    "name": "source",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.318115 27.49149, 27.467039 28.083276, 27.467039 28.083276, 30.318115 27.49149))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:37.209040", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:52:40", "op": "=="}])

        assert len(processing_gaps) == 1
        second_processing_gap_l1c = processing_gaps[0]

        # Check links with PROCESSING VALIDITY
        link_to_gap = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(second_processing_gap_l1c.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_gap) == 1

        link_from_gap = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(second_processing_gap_l1c.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert second_processing_gap_l1c.get_structured_values() == [{
            "values": [
                {
                    "value": "12.0",
                    "name": "detector",
                    "type": "double"
                },
                {
                    "value": "processing",
                    "name": "source",
                    "type": "text"
                },
                {
                    "value": "L1C",
                    "name": "level",
                    "type": "text"
                },
                {
                    "value": "S2A",
                    "name": "satellite",
                    "type": "text"
                },
                {
                    "name": "footprint_details",
                    "type": "object",
                    "values": [
                        {
                            "name": "footprint",
                            "type": "geometry",
                            "value": "POLYGON ((30.272837 27.326998, 27.426019 27.918371, 27.426019 27.918371, 30.272837 27.326998))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]
