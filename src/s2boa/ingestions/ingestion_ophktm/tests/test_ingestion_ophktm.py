"""
Automated tests for the ingestion of the REP_OPHKTM files

Written by DEIMOS Space S.L. (jubv)

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

class TestOphktm(unittest.TestCase):
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

    def test_insert_ophktm(self):

        filename = "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ophktm.ingestion_ophktm", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        events = self.query_eboa.get_events()

        assert len(events) == 1

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2020-10-15T12:56:41", "op": "=="}],
                                              reported_validity_stop_filters = [{"date": "2020-10-15T12:56:41", "op": "=="}],
                                              validity_start_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-10-15T13:13:02", "op": "=="}],
                                              processors = {"filter": "ingestion_ophktm.py", "op": "=="},
                                              dim_signatures = {"filter": "HKTM_PRODUCTION_VGS", "op": "=="},
                                              names = {"filter": "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF", "op": "=="})

        assert len(sources) == 1

        # Check HKMT production vgs event
        hktm_production_vgs_events = self.query_eboa.get_events(explicit_refs = {"filter": "S2B_OPER_PRD_HKTM___20201015T125434_20201015T125511_0001", "op": "=="},
                                                                gauge_names = {"filter": "HKTM_PRODUCTION_VGS", "op": "=="},
                                                                gauge_systems = {"filter": "SGS_", "op": "=="},
                                                                sources = {"filter": "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF", "op": "=="},
                                                                start_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}],
                                                                stop_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}])

        assert len(hktm_production_vgs_events) == 1
        hktm_production_vgs_event = hktm_production_vgs_events[0]

        assert hktm_production_vgs_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B"
            },
            {
                "name": "acquisition_center",
                "type": "text",
                "value": "SGS_"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "18854.0"
            }
        ]

        # Check HKMT production vgs annotation
        hktm_production_vgs_annotations = self.query_eboa.get_annotations(explicit_refs = {"filter": "S2B_OPER_PRD_HKTM___20201015T125434_20201015T125511_0001", "op": "=="},
                                                                          annotation_cnf_names = {"filter": "ACQUISITION_DETAILS", "op": "=="},
                                                                          annotation_cnf_systems = {"filter": "SGS_", "op": "=="},
                                                                          sources = {"filter": "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF", "op": "=="})

        assert len(hktm_production_vgs_annotations) == 1
        hktm_production_vgs_annotation = hktm_production_vgs_annotations[0]

        assert hktm_production_vgs_annotation.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B"
            },
            {
                "name": "acquisition_center",
                "type": "text",
                "value": "SGS_"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "18854.0"
            }
        ]
    
    def test_insert_ophktm_with_planning_and_rep_pass(self):

        filename = "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ophktm.ingestion_ophktm", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2020-10-15T12:56:41", "op": "=="}],
                                              reported_validity_stop_filters = [{"date": "2020-10-15T12:56:41", "op": "=="}],
                                              validity_start_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-10-15T13:13:02", "op": "=="}],
                                              processors = {"filter": "ingestion_ophktm.py", "op": "=="},
                                              dim_signatures = {"filter": "HKTM_PRODUCTION_VGS", "op": "=="},
                                              names = {"filter": "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF", "op": "=="})

        assert len(sources) == 1

        # Check HKMT production vgs event
        hktm_production_vgs_events = self.query_eboa.get_events(explicit_refs = {"filter": "S2B_OPER_PRD_HKTM___20201015T125434_20201015T125511_0001", "op": "=="},
                                                                gauge_names = {"filter": "HKTM_PRODUCTION_VGS", "op": "=="},
                                                                gauge_systems = {"filter": "SGS_", "op": "=="},
                                                                sources = {"filter": "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF", "op": "=="},
                                                                start_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}],
                                                                stop_filters = [{"date": "2020-10-15T12:56:41.000983", "op": "=="}])

        assert len(hktm_production_vgs_events) == 1
        hktm_production_vgs_event = hktm_production_vgs_events[0]

        assert hktm_production_vgs_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B"
            },
            {
                "name": "acquisition_center",
                "type": "text",
                "value": "SGS_"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "18854.0"
            }
        ]

        # Check links with PLANNED_PLAYBACK
        plannned_playback_linking_to_hktm_production_vgs = self.query_eboa.get_linking_events(event_uuids = {"filter": str(hktm_production_vgs_event.event_uuid), "op": "=="},
                                                          link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})

        assert len(plannned_playback_linking_to_hktm_production_vgs["linking_events"]) == 1

        planned_playback = plannned_playback_linking_to_hktm_production_vgs["linking_events"][0]

        hktm_production_vgs_linking_to_plannned_playback = self.query_eboa.get_linking_events(event_uuids = {"filter": str(planned_playback.event_uuid), "op": "=="},
                                                          link_names = {"filter": "HKTM_PRODUCTION_VGS", "op": "=="})

        assert len(hktm_production_vgs_linking_to_plannned_playback["linking_events"]) == 1

        # Check links with PLAYBACK_VALIDITY_3
        playback_validity_linking_to_hktm_production_vgs = self.query_eboa.get_linking_events(event_uuids = {"filter": str(hktm_production_vgs_event.event_uuid), "op": "=="},
                                                          link_names = {"filter": "PLAYBACK_VALIDITY", "op": "=="})

        assert len(playback_validity_linking_to_hktm_production_vgs["linking_events"]) == 1

        playback_validity = playback_validity_linking_to_hktm_production_vgs["linking_events"][0]

        hktm_production_vgs_linking_to_playback_validity = self.query_eboa.get_linking_events(event_uuids = {"filter": str(playback_validity.event_uuid), "op": "=="},
                                                          link_names = {"filter": "HKTM_PRODUCTION_VGS", "op": "=="})

        assert len(hktm_production_vgs_linking_to_playback_validity["linking_events"]) == 1
        
        # Check HKMT production vgs annotation
        hktm_production_vgs_annotations = self.query_eboa.get_annotations(explicit_refs = {"filter": "S2B_OPER_PRD_HKTM___20201015T125434_20201015T125511_0001", "op": "=="},
                                                                          annotation_cnf_names = {"filter": "ACQUISITION_DETAILS", "op": "=="},
                                                                          annotation_cnf_systems = {"filter": "SGS_", "op": "=="},
                                                                          sources = {"filter": "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF", "op": "=="})

        assert len(hktm_production_vgs_annotations) == 1
        hktm_production_vgs_annotation = hktm_production_vgs_annotations[0]

        assert hktm_production_vgs_annotation.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B"
            },
            {
                "name": "acquisition_center",
                "type": "text",
                "value": "SGS_"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "18854.0"
            }
        ]
