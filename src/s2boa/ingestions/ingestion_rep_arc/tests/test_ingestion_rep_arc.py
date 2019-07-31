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
                                                   annotation_cnf_names = {"op": "like", "filter": "PRODUCTION_BASELINE"})

        assert len(baseline) == 1

        #Check definite footprint
        definite_footprint = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "FOOTPRINT"},
                                                     explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085229_D01_N02.06"})

        assert definite_footprint[0].get_structured_values() == [{
            'type': 'object',
            'name': 'details',
            'values': [{'type': 'geometry',
                'name': 'footprint',
                'value': 'POLYGON ((27.5923694065675 28.6897912912051, 27.5923694065675 28.6897912912051, 27.8617502445779 28.6464983273278, 27.7690524083984 28.2803979779816, 27.4991925556512 28.322475522552, 27.5923694065675 28.6897912912051))'
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.419825 27.857979, 30.359831 27.641211, 30.300019 27.42442, 30.240408 27.207604, 30.180994 26.990764, 30.12177 26.773901, 30.062725 26.557015, 30.003871 26.340105, 29.945205 26.123173, 29.886715 25.906218, 29.8284 25.689241, 29.770267 25.472241, 29.712313 25.25522, 29.654521 25.038177, 29.596901 24.821113, 29.539455 24.604027, 29.482176 24.386921, 29.425052 24.169794, 29.368095 23.952647, 29.311302 23.735479, 29.254664 23.518292, 29.198178 23.301085, 29.141851 23.083858, 29.08568 22.866612, 29.029652 22.649347, 28.973774 22.432063, 28.918046 22.214761, 28.862467 21.99744, 28.807021 21.780101, 26.083887 22.359895, 26.135173 22.577612, 26.186525 22.795319, 26.237978 23.013011, 26.289535 23.230691, 26.341189 23.448358, 26.392922 23.666012, 26.444764 23.883653, 26.496717 24.10128, 26.548761 24.318893, 26.600902 24.536493, 26.653158 24.754079, 26.705532 24.97165, 26.757991 25.189208, 26.810565 25.406751, 26.863261 25.624279, 26.916075 25.841792, 26.968981 26.059292, 27.022014 26.276775, 27.075177 26.494243, 27.128453 26.711696, 27.181839 26.929133, 27.23536 27.146555, 27.289018 27.363959, 27.342783 27.581349, 27.396678 27.798722, 27.450716 28.016078, 27.504897 28.233417, 27.559182 28.450741, 30.419825 27.857979))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.419825 27.857979, 30.359831 27.641211, 30.300019 27.42442, 30.240408 27.207604, 30.180994 26.990764, 30.12177 26.773901, 30.062725 26.557015, 30.003871 26.340105, 29.945205 26.123173, 29.886715 25.906218, 29.8284 25.689241, 29.770267 25.472241, 29.712313 25.25522, 29.654521 25.038177, 29.596901 24.821113, 29.539455 24.604027, 29.482176 24.386921, 29.425052 24.169794, 29.368095 23.952647, 29.311302 23.735479, 29.254664 23.518292, 29.198178 23.301085, 29.141851 23.083858, 29.08568 22.866612, 29.029652 22.649347, 28.973774 22.432063, 28.918046 22.214761, 28.862467 21.99744, 28.807021 21.780101, 26.083887 22.359895, 26.135173 22.577612, 26.186525 22.795319, 26.237978 23.013011, 26.289535 23.230691, 26.341189 23.448358, 26.392922 23.666012, 26.444764 23.883653, 26.496717 24.10128, 26.548761 24.318893, 26.600902 24.536493, 26.653158 24.754079, 26.705532 24.97165, 26.757991 25.189208, 26.810565 25.406751, 26.863261 25.624279, 26.916075 25.841792, 26.968981 26.059292, 27.022014 26.276775, 27.075177 26.494243, 27.128453 26.711696, 27.181839 26.929133, 27.23536 27.146555, 27.289018 27.363959, 27.342783 27.581349, 27.396678 27.798722, 27.450716 28.016078, 27.504897 28.233417, 27.559182 28.450741, 30.419825 27.857979))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.452534 27.975823, 30.392614 27.75977, 30.332896 27.543693, 30.273379 27.327592, 30.214044 27.111468, 30.1549 26.89532, 30.095949 26.679148, 30.037187 26.462953, 29.978597 26.246736, 29.920192 26.030496, 29.861972 25.814233, 29.803925 25.597949, 29.746048 25.381643, 29.688348 25.165315, 29.630823 24.948965, 29.573458 24.732595, 29.51626 24.516204, 29.45923 24.299792, 29.402366 24.083359, 29.345652 23.866907, 29.289101 23.650434, 29.23271 23.433942, 29.176471 23.21743, 29.12038 23.000899, 29.064444 22.784349, 29.008661 22.56778, 28.953019 22.351192, 28.897521 22.134586, 28.842171 21.917962, 28.786966 21.701319, 28.731891 21.484659, 26.01434 22.063948, 26.065337 22.280978, 26.1164 22.497996, 26.16756 22.715002, 26.218822 22.931994, 26.270178 23.148974, 26.321611 23.365942, 26.37315 23.582897, 26.424797 23.799838, 26.476531 24.016766, 26.52836 24.233681, 26.580303 24.450582, 26.632359 24.667468, 26.684496 24.884342, 26.736747 25.101201, 26.789118 25.318046, 26.841599 25.534876, 26.894174 25.751692, 26.946873 25.968493, 26.999698 26.185279, 27.052627 26.40205, 27.10567 26.618806, 27.158843 26.835546, 27.212151 27.052269, 27.265555 27.268979, 27.319093 27.485672, 27.372771 27.702348, 27.426579 27.919008, 27.480497 28.135652, 27.53456 28.35228, 27.58877 28.568889, 30.452534 27.975823))"
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
                            "value": "POLYGON ((30.318662 27.492084, 27.467602 28.083913, 27.467602 28.083913, 30.318662 27.492084))"
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
                            "value": "POLYGON ((30.273379 27.327592, 27.426579 27.919008, 27.426579 27.919008, 30.273379 27.327592))"
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
                            "value": "POLYGON ((30.318662 27.492084, 27.467602 28.083913, 27.467602 28.083913, 30.318662 27.492084))"
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
                            "value": "POLYGON ((30.273379 27.327592, 27.426579 27.919008, 27.426579 27.919008, 30.273379 27.327592))"
                        }
                    ]
                }
            ],
            "name": "details",
            "type": "object"
        }]
