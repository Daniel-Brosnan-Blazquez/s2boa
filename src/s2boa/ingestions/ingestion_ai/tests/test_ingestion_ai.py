"""
Automated tests for the ingestion of the REP_OPAI files

Written by DEIMOS Space S.L. (femd)

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

class TestAi(unittest.TestCase):
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

    def test_rep_ai(self):

        filename = "S2__OPER_REP_OPAI___MPS__20180721T130001_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ai.ingestion_ai", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T01:00:01", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-21T13:00:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T13:00:01", "op": "=="}],
                                              processors = {"filter": "ingestion_ai.py", "op": "like"},
                                              names = {"filter": "S2__OPER_REP_OPAI___MPS__20180721T130001_RIPPED.EOF", "op": "like"})

        assert len(sources) == 1

        #Check definite archiving_time
        definite_archiving_time = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "ARCHIVING_TIME"},
                                                     explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L1C_TC_MPS__20180721T001557_A016071_T14XMR_N02.06"})

        assert definite_archiving_time[0].get_structured_values() == [
            {'type': 'timestamp',
             'name': 'archiving_time',
             'value': '2018-07-21T01:00:36'
            }]

        #Check archiving_time
        archiving_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "ARCHIVING_TIME"})

        assert len(archiving_times) == 2

    def test_rep_ai_hktm_only(self):

        filename = "S2__OPER_REP_OPAI_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ai.ingestion_ai", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 2

        events = self.query_eboa.get_events()

        assert len(events) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                             validity_stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T07:05:18", "op": "=="}],
                                             processors = {"filter": "ingestion_ai.py", "op": "=="},
                                              dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             names = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-01-29T01:05:02", "op": "=="}],
                                             validity_stop_filters = [{"date": "2020-01-29T07:05:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T07:05:18", "op": "=="}],
                                             processors = {"filter": "ingestion_ai.py", "op": "=="},
                                              dim_signatures = {"filter": "ARCHIVING", "op": "=="},
                                             names = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="})

        assert len(sources) == 1
        
        # Check production playback validity
        production_playback_validities = self.query_eboa.get_events(explicit_refs = {"filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001", "op": "like"},
                                                                    gauge_names = {"filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY", "op": "like"},
                                                                    sources = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="},
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

        # Check archiving time
        archiving_time = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "ARCHIVING_TIME"},
                                                         explicit_refs = {"op": "like", "filter": "S2A_OPER_PRD_HKTM___20200129T032508_20200129T032513_0001"})

        assert archiving_time[0].get_structured_values() == [
            {'type': 'timestamp',
             'name': 'archiving_time',
             'value': '2020-01-29T03:27:51'
            }]

        # Check number of annotations
        archiving_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "ARCHIVING_TIME"})

        assert len(archiving_times) == 1

    def test_rep_ai_hktm_with_nppf_rep_pass(self):

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

        filename = "S2__OPER_REP_OPAI_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ai.ingestion_ai", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 9

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                             validity_stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T07:05:18", "op": "=="}],
                                             processors = {"filter": "ingestion_ai.py", "op": "=="},
                                              dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                             names = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-01-29T01:05:02", "op": "=="}],
                                             validity_stop_filters = [{"date": "2020-01-29T07:05:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T07:05:18", "op": "=="}],
                                             processors = {"filter": "ingestion_ai.py", "op": "=="},
                                              dim_signatures = {"filter": "ARCHIVING", "op": "=="},
                                             names = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="})

        assert len(sources) == 1
        
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
            }
        ]

    def test_rep_ai_hktm_with_rep_pass(self):

        filename = "S2A_OPER_REP_PASS_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_OPAI_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ai.ingestion_ai", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 5

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-01-29T03:25:08", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-01-29T03:25:13", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T07:05:18", "op": "=="}],
                                              processors = {"filter": "ingestion_ai.py", "op": "=="},
                                              dim_signatures = {"filter": "PROCESSING_S2A", "op": "=="},
                                              names = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="})

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-01-29T01:05:02", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-01-29T07:05:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-01-29T07:05:18", "op": "=="}],
                                              processors = {"filter": "ingestion_ai.py", "op": "=="},
                                              dim_signatures = {"filter": "ARCHIVING", "op": "=="},
                                              names = {"filter": "S2__OPER_REP_OPAI_HKTM.EOF", "op": "=="})

        assert len(sources) == 1
        
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
        
