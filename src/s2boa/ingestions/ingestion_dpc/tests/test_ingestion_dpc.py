"""
Automated tests for the ingestion of the DPC files

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

class TestDpcIngestion(unittest.TestCase):
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

    def test_dpc_report_L0_only(self):

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 8

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1
        # Check step infos
        step_infos = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "STEP_INFO", "op": "like"})

        assert len(step_infos) == 14

        # Check mrf validities
        mrf_validities = self.query_eboa.get_events(sources = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"},
                                                           gauge_names = {"filter": "MRF_VALIDITY", "op": "like"})

        assert len(mrf_validities) == 27

        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l0 = processing_validities[0]

        assert processing_validity_l0.get_structured_values() == [
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
                "value": "MPS_",
                "type": "text",
                "name": "processing_centre"
            },
            {
                "value": "NO_MATCHED_PLANNED_IMAGING",
                "type": "text",
                "name": "matching_plan_status"
            },
            {
                "value": "NO_MATCHED_ISP_VALIDITY",
                "type": "text",
                "name": "matching_reception_status"
            }
        ]


    def test_dpc_report_and_rep_pass_L0_3_scenes(self):

        filename = "S2B_REP_PASS_3_SCENES.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        
        filename = "S2B_OPER_REP_OPDPC_L0_3_SCENES.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 12

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2019-07-15T15:10:47", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2019-07-15T15:10:54", "op": "=="}],
                                              validity_start_filters = [{"date": "2019-07-15T15:10:47", "op": "=="}],
                                             validity_stop_filters = [{"date": "2019-07-15T15:10:59", "op": "=="}],
                                              generation_time_filters = [{"date": "2019-07-15T19:59:38", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2B", "op": "=="},
                                             names = {"filter": "S2B_OPER_REP_OPDPC_L0_3_SCENES.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2019-07-15T15:10:47", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2019-07-15T15:10:54", "op": "=="}],
                                              validity_start_filters = [{"date": "2019-07-15T15:10:47", "op": "=="}],
                                             validity_stop_filters = [{"date": "2019-07-15T19:59:32.335", "op": "=="}],
                                              generation_time_filters = [{"date": "2019-07-15T19:59:38", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2B", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2B_OPER_REP_OPDPC_L0_3_SCENES.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2019-07-15T15:10:47", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2019-07-15T15:10:54", "op": "=="}],
                                              validity_start_filters = [{"date": "2009-12-10T23:51:34.000", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2019-07-15T19:59:38", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2B_OPER_REP_OPDPC_L0_3_SCENES.EOF", "op": "like"})

        assert len(sources) == 1


    def test_dpc_report_L0_plan(self):

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

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]
        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1

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

        assert processing_validity_l0.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]
        
        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l0 = planning_completeness[0]

        assert planning_completeness_l0.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

    def test_dpc_report_L0_with_rep_pass(self):

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

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

        assert processing_validity_l0.get_structured_values() == [
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
                "value": "MPS_",
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
        ]

    def test_dpc_report_L1A_L1B_only(self):

        filename = "S2A_OPER_REP_OPDPC_L0_L1A_L1B.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 8

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2019-07-15T18:04:03", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2019-07-15T18:06:38", "op": "=="}],
                                              validity_start_filters = [{"date": "2019-07-15T18:04:03", "op": "=="}],
                                             validity_stop_filters = [{"date": "2019-07-15T23:18:02.353", "op": "=="}],
                                              generation_time_filters = [{"date": "2019-07-15T23:18:12", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0_L1A_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2019-07-15T18:04:03", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2019-07-15T18:06:38", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2019-07-15T23:18:12", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0_L1A_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        processing_validities = self.query_eboa.get_events(gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(processing_validities) == 2
        
    def test_dpc_report_L1C_only(self):

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 8

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        processing_validities = self.query_eboa.get_events(gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(processing_validities) == 0


        ers = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%_L1C_%", "op": "like"})

        assert len(ers) == 63

        linking_ers = self.query_eboa.get_linking_explicit_refs(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "=="}, link_names = {"filter": ["TILE", "TCI"], "op": "in"})
        
        assert len(linking_ers["linking_explicit_refs"]) == 62

    def test_dpc_report_L1C_with_L0(self):

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1
        
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1c = processing_validities[0]

        assert processing_validity_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
        ]

        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1c = planning_completeness[0]

        assert planning_completeness_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
        ]

    def test_dpc_report_L1C_with_L0_plan(self):
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

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1
        
        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]

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

        assert processing_validity_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1c = planning_completeness[0]

        assert planning_completeness_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]
        
        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1


    def test_dpc_report_L1C_with_L0_plan_rep_pass(self):

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

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

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

        assert processing_validity_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

    def test_dpc_report_L1C_with_L0_rep_pass(self):

        filename = "S2A_REP_PASS_NO_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                              dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                              dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                              dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                              dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        isp_validity = self.query_eboa.get_events(gauge_names = {"filter": "ISP_VALIDITY", "op": "like"})[0]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1c = processing_validities[0]

        # Check links with PROCESSING VALIDITY
        link_to_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_isp_validity) == 1

        link_from_isp_validity = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "ISP_VALIDITY", "op": "like"})

        assert len(link_from_isp_validity) == 1

        assert processing_validity_l1c.get_structured_values() == [
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
                "value": "MPS_",
                "name": "processing_centre",
                "type": "text"
            },
            {
                "value": "NO_MATCHED_PLANNED_IMAGING",
                "name": "matching_plan_status",
                "type": "text"
            },
            {
                "value": "MATCHED_ISP_VALIDITY",
                "name": "matching_reception_status",
                "type": "text"
            },
            {
                "value": "16078.0",
                "name": "downlink_orbit",
                "type": "double"
            }
        ]

    def test_insert_dpc_L0_L1B_L1C_with_plan_and_rep_pass(self):

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

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0_L1B.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check sources
        # L0
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2000-12-10 23:51:34", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:43:34", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"})

        assert len(sources) == 1

        # L1B
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:55:47", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:55:47", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T10:55:38.778000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:55:47", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "9999-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T10:55:47", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L0_L1B.EOF", "op": "like"})

        assert len(sources) == 1

        # L1C
        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             validity_stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             processors = {"filter": "ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              validity_start_filters = [{"date": "1983-01-01T00:00:00", "op": "=="}],
                                             validity_stop_filters = [{"date": "2100-01-01T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:00:45", "op": "=="}],
                                             processors = {"filter": "configuration_ingestion_dpc.py", "op": "like"},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_L1B_L1C.EOF", "op": "like"})

        assert len(sources) == 1
        
        imaging_plan = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "like"})[0]
        isp_validity = self.query_eboa.get_events(gauge_names = {"filter": "ISP_VALIDITY", "op": "like"})[0]

        
        # Check step infos
        step_infos = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "STEP_INFO", "op": "like"})

        assert len(step_infos) == 14

        # Check mrf validities
        mrf_validities = self.query_eboa.get_events(sources = {"filter": "S2A_OPER_REP_OPDPC_L0U_L0.EOF", "op": "like"},
                                                           gauge_names = {"filter": "MRF_VALIDITY", "op": "like"})

        assert len(mrf_validities) == 27

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

        assert processing_validity_l0.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

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

        assert processing_validity_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

        # Check ISP validity completeness
        isp_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0%", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(isp_completeness) == 2
        isp_completeness_l0 = isp_completeness[0]

        isp_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B%", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(isp_completeness) == 2
        isp_completeness_l1b = isp_completeness[0]

        isp_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C%", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(isp_completeness) == 2
        isp_completeness_l1c = isp_completeness[0]
        
        # Check planning completeness
        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l0 = planning_completeness[0]

        assert planning_completeness_l0.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0%", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0%", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1b = planning_completeness[0]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        planning_completeness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}])

        assert len(planning_completeness) == 1
        planning_completeness_l1c = planning_completeness[0]

        assert planning_completeness_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]
        
        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_statuses = [event for event in missing_planning_completeness if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(missing_planning_completeness_statuses) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        # Check timeliness
        timeliness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "TIMELINESS", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T10:39:13.800000", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T10:43:26.741000", "op": "=="}])

        assert len(timeliness) == 1
        timeliness_l0 = timeliness[0]

        timeliness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "TIMELINESS", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T10:42:47.800000", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T10:55:38.778000", "op": "=="}])

        assert len(timeliness) == 1
        timeliness_l1b = timeliness[0]

        timeliness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "TIMELINESS", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T10:50:39.900000", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T11:00:38.066000", "op": "=="}])

        assert len(timeliness) == 1
        timeliness_l1c = timeliness[0]

    def test_dpc_gaps_L1C_with_L0_plan_rep_pass(self):

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

        filename = "S2A_OPER_REP_OPDPC_L0U_L0_WITH_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check processing validities
        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                                           stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l0 = processing_validities[0]

        assert processing_validity_l0.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

        processing_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "like"},
                                             start_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:54:19", "op": "=="}])

        assert len(processing_validities) == 1
        processing_validity_l1c = processing_validities[0]

        assert processing_validity_l1c.get_structured_values() == [
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
                "value": "MPS_",
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
                "name": "imaging_mode",
                "type": "text",
                "value": "NOMINAL"
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
        ]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert len(processing_gaps) == 3

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

        assert first_processing_gap_l0.get_structured_values() == [
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
                        "value": "POLYGON ((30.318662 27.492084, 27.467602 28.083913, 27.467602 28.083913, 30.318662 27.492084))"
                    }
                ]
            }
        ]

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

        assert second_processing_gap_l0.get_structured_values() == [
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
                        "value": "POLYGON ((30.273379 27.327592, 27.426579 27.919008, 27.426579 27.919008, 30.273379 27.327592))"
                    }
                ]
            }
        ]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"},
                                                     value_filters = [{"name": {"filter": "detector", "op": "like"}, "type": "double", "value": {"filter": "1", "op": "=="}}],
                                                     start_filters = [{"date": "2018-07-21T08:52:42", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:52:44", "op": "=="}])

        assert len(processing_gaps) == 1
        third_processing_gap_l0 = processing_gaps[0]

        # Check links with PROCESSING VALIDITY
        link_to_gap = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(third_processing_gap_l0.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_gap) == 1

        link_from_gap = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l0.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(third_processing_gap_l0.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert third_processing_gap_l0.get_structured_values() == [
            {
                "value": "1.0",
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
                        "value": "POLYGON ((30.208661 27.091819, 27.36789 27.682651, 27.36789 27.682651, 30.208661 27.091819))"
                    }
                ]
            }
        ]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert len(processing_gaps) == 3


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

        assert first_processing_gap_l1c.get_structured_values() == [
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
                        "value": "POLYGON ((30.318662 27.492084, 27.467602 28.083913, 27.467602 28.083913, 30.318662 27.492084))"
                    }
                ]
            }
        ]

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

        assert second_processing_gap_l1c.get_structured_values() == [
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
                        "value": "POLYGON ((30.273379 27.327592, 27.426579 27.919008, 27.426579 27.919008, 30.273379 27.327592))"
                    }
                ]
            }
        ]

        processing_gaps = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06", "op": "like"},
                                                           gauge_names = {"filter": "PROCESSING_GAP", "op": "like"},
                                                     value_filters = [{"name": {"filter": "detector", "op": "like"}, "type": "double", "value": {"filter": "1", "op": "=="}}],
                                                     start_filters = [{"date": "2018-07-21T08:52:42", "op": "=="}],
                                             stop_filters = [{"date": "2018-07-21T08:52:44", "op": "=="}])

        assert len(processing_gaps) == 1
        third_processing_gap_l1c = processing_gaps[0]

        # Check links with PROCESSING VALIDITY
        link_to_gap = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(third_processing_gap_l1c.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_VALIDITY", "op": "like"})

        assert len(link_to_gap) == 1

        link_from_gap = self.query_eboa.get_event_links(event_uuids = {"filter": [str(processing_validity_l1c.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(third_processing_gap_l1c.event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PROCESSING_GAP", "op": "like"})

        assert third_processing_gap_l1c.get_structured_values() == [
            {
                "value": "1.0",
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
                        "value": "POLYGON ((30.208661 27.091819, 27.36789 27.682651, 27.36789 27.682651, 30.208661 27.091819))"
                    }
                ]
            }
        ]

    def test_insert_2_dpc_L0_L1B_L1C_L2A_with_plan_and_rep_pass(self):

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

        filename = "S2A_OPER_REP_OPDPC_L0U_L0.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0_L1B.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1C_L2A.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0U_L0_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L0_L1B_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_L1B_L1C_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                           value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}])

        assert len(missing_planning_completeness) == 2

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T08:52:29", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_2 = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T09:06:46", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness_2) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                           value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}])

        assert len(missing_planning_completeness) == 2

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_2 = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T09:06:41", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness_2) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                           value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}])

        assert len(missing_planning_completeness) == 2

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_2 = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T09:06:41", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness_2) == 1

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op": "like"},
                                                           value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}])

        assert len(missing_planning_completeness) == 2

        missing_planning_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T08:36:08.255634", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T08:52:31", "op": "=="}])

        assert len(missing_planning_completeness) == 1

        missing_planning_completeness_2 = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A", "op": "like"},
                                                                   value_filters = [{"name": {"filter": "status", "op": "like"}, "type": "text", "value": {"filter": "MISSING", "op": "=="}}],
                                                                   start_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                                                   stop_filters = [{"date": "2018-07-21T09:08:50.195941", "op": "=="}])

        assert len(missing_planning_completeness_2) == 1

        # Check number of components of the datastrips
        number_of_components = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "NUMBER_OF_GRANULES"},
                                                               explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"})

        assert len(number_of_components) == 1

        assert number_of_components[0].get_structured_values() == [
            {
                "name": "number",
                "type": "double",
                "value": "360.0"
            }
        ]
        number_of_components = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "NUMBER_OF_GRANULES"},
                                                               explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L1B_DS_MPS__20180721T104253_S20180721T085229_N02.06"})

        assert len(number_of_components) == 1

        assert number_of_components[0].get_structured_values() == [
            {
                "name": "number",
                "type": "double",
                "value": "324.0"
            }
        ]
        number_of_components = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "NUMBER_OF_TILES"},
                                                               explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L1C_DS_MPS__20180721T104253_S20180721T085229_N02.06"})

        assert len(number_of_components) == 1

        assert number_of_components[0].get_structured_values() == [
            {
                "name": "number",
                "type": "double",
                "value": "31.0"
            }
        ]
        number_of_components = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "NUMBER_OF_TILES"},
                                                               explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L2A_DS_MPS__20180721T110122_S20180721T085229_N02.08"})

        assert len(number_of_components) == 1

        assert number_of_components[0].get_structured_values() == [
            {
                "name": "number",
                "type": "double",
                "value": "19.0"
            }
        ]

    def test_dpc_report_hktm_only(self):

        filename = "S2A_OPER_REP_OPDPC_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 4

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                              validity_start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                             validity_stop_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_HKTM.EOF", "op": "=="})

        assert len(sources) == 1

        # Check production playback validity
        production_playback_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                           gauge_names = {"filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                                           stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}])

        assert len(production_playback_validities) == 1
        production_playback_validity = production_playback_validities[0]

        assert production_playback_validity.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            }
        ]

        # Check timeliness
        timeliness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                           gauge_names = {"filter": "TIMELINESS", "op": "like"},
                                                           start_filters = [{"date": "2020-01-29T03:25:33.600000", "op": "=="}],
                                                           stop_filters = [{"date": "2020-01-29T03:27:17.379000", "op": "=="}])

        assert len(timeliness) == 1

        assert timeliness[0].get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            }
        ]

    def test_dpc_report_hktm_duplicated(self):

        filename = "S2A_OPER_REP_OPDPC_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_OPDPC_HKTM_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 5

        events = self.query_eboa.get_events()

        assert len(events) == 2

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                             reported_validity_stop_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                              validity_start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                             validity_stop_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T03:27:24", "op": "=="}],
                                             processors = {"filter": "ingestion_dpc.py", "op": "=="},
                                             names = {"filter": "S2A_OPER_REP_OPDPC_HKTM.EOF", "op": "=="})

        assert len(sources) == 1

        # Check production playback validity
        production_playback_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                                    gauge_names = {"filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY", "op": "like"},
                                                                    sources = {"filter": "S2A_OPER_REP_OPDPC_HKTM.EOF", "op": "=="},
                                                                    start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                                                    stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}])

        assert len(production_playback_validities) == 1
        production_playback_validity = production_playback_validities[0]

        assert production_playback_validity.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            }
        ]

        # Check timeliness
        timeliness = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                gauge_names = {"filter": "TIMELINESS", "op": "like"},
                                                sources = {"filter": "S2A_OPER_REP_OPDPC_HKTM.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-01-29T03:25:33.600000", "op": "=="}],
                                                stop_filters = [{"date": "2020-01-29T03:27:17.379000", "op": "=="}])

        assert len(timeliness) == 1

        assert timeliness[0].get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            }
        ]

    def test_dpc_report_hktm_with_nppf_rep_pass(self):

        filename = "S2A_OPER_MPL__NPPF_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]        

        filename = "S2A_OPER_REP_PASS_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        filename = "S2A_OPER_REP_OPDPC_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 11
        
        # Check production playback validity
        production_playback_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                           gauge_names = {"filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                                           stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}])

        assert len(production_playback_validities) == 1
        production_playback_validity = production_playback_validities[0]

        # Check links with plan
        planned_playback = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})
        assert len(planned_playback) == 1
        
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(production_playback_validity.event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "HKTM_PRODUCTION", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(production_playback_validity.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})

        assert len(link_from_plan) == 1

        # Check links with acquisition
        playback_validity = self.query_eboa.get_events(gauge_names = {"filter": "PLAYBACK_VALIDITY_3", "op": "=="})
        assert len(playback_validity) == 1
        
        link_to_playback_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(production_playback_validity.event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(playback_validity[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "HKTM_PRODUCTION", "op": "like"})

        assert len(link_to_playback_validity) == 1

        link_from_playback_validity = self.query_eboa.get_event_links(event_uuids = {"filter": [str(production_playback_validity.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(playback_validity[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLAYBACK_VALIDITY", "op": "=="})

        assert len(link_from_playback_validity) == 1

        assert production_playback_validity.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "24039.0"
            },
            {"name": "footprint_details",
             "type": "object",
             "values": [{"name": "footprint",
                         "type": "geometry",
                         "value": "POLYGON ((158.123595 77.583848, 157.023979 77.400386, 148.273393 79.3361, 149.402469 79.551652, 158.123595 77.583848))"}]}
        ]

    def test_dpc_report_hktm_with_rep_pass(self):

        filename = "S2A_OPER_REP_PASS_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]
        
        filename = "S2A_OPER_REP_OPDPC_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dpc.ingestion_dpc_l1c_l2a_no_wait", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 7
        
        # Check production playback validity
        production_playback_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                           gauge_names = {"filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY", "op": "like"},
                                                           start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                                           stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}])

        assert len(production_playback_validities) == 1
        production_playback_validity = production_playback_validities[0]

        # Check links with acquisition
        playback_validity = self.query_eboa.get_events(gauge_names = {"filter": "PLAYBACK_VALIDITY_3", "op": "=="})
        assert len(playback_validity) == 1
        
        link_to_playback_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(production_playback_validity.event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(playback_validity[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "HKTM_PRODUCTION", "op": "like"})

        assert len(link_to_playback_validity) == 1

        link_from_playback_validity = self.query_eboa.get_event_links(event_uuids = {"filter": [str(production_playback_validity.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(playback_validity[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLAYBACK_VALIDITY", "op": "=="})

        assert len(link_from_playback_validity) == 1

        assert production_playback_validity.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "24039.0"
            }
        ]
