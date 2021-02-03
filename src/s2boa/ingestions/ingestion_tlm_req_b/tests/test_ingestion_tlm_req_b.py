"""
Automated tests for the ingestion of the TLM_REQ_B files

Written by DEIMOS Space S.L. (dibb)

module s2boa
"""
import pdb
# Import python utilities
import os
import sys
import unittest
import datetime

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

class TestTlmReqB(unittest.TestCase):
    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Create session to connect to the database
        self.session = Session()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

    def tearDown(self):
        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()
        self.session.close()

    def test_insert_tlm_req(self):
        
        filename = "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_tlm_req_b.ingestion_tlm_req_b", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        sources = self.query_eboa.get_sources()
        assert len(sources) == 1

        # Check number of events generated
        events = self.query_eboa.get_events()
        assert len(events) == 7264

        # Check source
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-11-26T00:00:00", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-11-27T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-11-26T00:00:00", "op": "=="}],
                                              processors = {"filter": "ingestion_tlm_req_b.py", "op": "=="},
                                              dim_signatures = {"filter": "MEMORY_EVOLUTION_S2B", "op": "=="},
                                              names = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="})

        assert len(sources) == 1

        # Check memory event
        tlm_memory_events = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:00.131650", "op": "=="}])

        assert len(tlm_memory_events) == 1
        
        tlm_memory_event = tlm_memory_events[0]
        assert tlm_memory_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B"
            },
            {
                "name": "number_of_scenes",
                "type": "double",
                "value": "7.0"
            }
        ]

        # Check last memory event ends at validity stop
        tlm_memory_events = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="},
                                                stop_filters = [{"date": "2020-11-27T00:00:00", "op": "=="}])

        assert len(tlm_memory_events) == 1
        
        tlm_memory_event = tlm_memory_events[0]
        assert tlm_memory_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B"
            },
            {
                "name": "number_of_scenes",
                "type": "double",
                "value": "204.0"
            }
        ]

        # Check discrepancy events with difference
        tlm_discrepancy_events = self.query_eboa.get_events(gauge_names = {"filter": "DISCREPANCY_CHANNEL_2_LAST_REPLAYED_SCENE", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T01:02:15.133892", "op": "=="}])

        assert len(tlm_discrepancy_events) == 1
        tlm_discrepancy_event = tlm_discrepancy_events[0]

        assert tlm_discrepancy_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            },
            {
                "name": "number_of_scenes",
                "type": "double",
                "value": "1.0"
            }
        ]

        # Check that no discrepancy event exists if there is no discrepancy
        tlm_no_discrepancy_events = self.query_eboa.get_events(gauge_names = {"filter": "DISCREPANCY_CHANNEL_2_NRT_MEMORY_OCCUOATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T01:02:15.133892", "op": "=="}])

        assert len(tlm_no_discrepancy_events) == 0

        # Check gap events
        tlm_gap_events = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_CHANNEL_1_GAP", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T06:36:25.132008", "op": "=="}])

        assert len(tlm_gap_events) == 1
        tlm_gap_event = tlm_gap_events[0]

        assert tlm_gap_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            }
        ]

        #Check that no gap event exists if there is no gap
        tlm_no_gap_events = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_CHANNEL_1_GAP", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:00.131650", "op": "=="}])

        assert len(tlm_no_gap_events) == 0

    def test_insert_tlm_req_with_discrepancy_and_gaps(self):

        filename = "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_tlm_req_b.ingestion_tlm_req_b", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        sources = self.query_eboa.get_sources()
        assert len(sources) == 1

        # Check number of events generated
        events = self.query_eboa.get_events()
        assert len(events) == 7271 

        # Check source
        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-11-26T00:00:00", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-11-27T00:00:00", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-11-26T00:00:00", "op": "=="}],
                                              processors = {"filter": "ingestion_tlm_req_b.py", "op": "=="},
                                              dim_signatures = {"filter": "MEMORY_EVOLUTION_S2B", "op": "=="},
                                              names = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="})

        assert len(sources) == 1

        # Check that first nominal memory event is missing
        tlm_memory_events = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:00.131650", "op": "=="}])

        assert len(tlm_memory_events) == 0

        # Check discrepancy event - first event
        tlm_discrepancy_events = self.query_eboa.get_events(gauge_names = {"filter": "DISCREPANCY_CHANNEL_2_NRT_MEMORY_OCCUPATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:00.131650", "op": "=="}])

        assert len(tlm_discrepancy_events) == 1
        tlm_discrepancy_event = tlm_discrepancy_events[0]

        assert tlm_discrepancy_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            },
            {
                "name": "number_of_scenes",
                "type": "double",
                "value": "-1.0"
            }
        ]

        # Check discrepancy event - middle event
        tlm_discrepancy_events = self.query_eboa.get_events(gauge_names = {"filter": "DISCREPANCY_CHANNEL_2_NOMINAL_MEMORY_OCCUPATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:10.131509", "op": "=="}])

        assert len(tlm_discrepancy_events) == 1
        tlm_discrepancy_event = tlm_discrepancy_events[0]

        assert tlm_discrepancy_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            },
            {
                "name": "number_of_scenes",
                "type": "double",
                "value": "5.0"
            }
        ]

        # Check discrepancy event - last event
        tlm_discrepancy_events = self.query_eboa.get_events(gauge_names = {"filter": "DISCREPANCY_CHANNEL_2_LAST_REPLAYED_SCENE", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T23:59:55.132073", "op": "=="}])

        assert len(tlm_discrepancy_events) == 1
        tlm_discrepancy_event = tlm_discrepancy_events[0]

        assert tlm_discrepancy_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            },
            {
                "name": "number_of_scenes",
                "type": "double",
                "value": "3.0"
            }
        ]

        # Check that no discrepancy event exists when there is a gap in only one of the channels
        # Check gap in first event
        tlm_gap_event = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_CHANNEL_1_GAP", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:00.00", "op": "=="}])

        assert len(tlm_gap_event) == 1
        tlm_gap_event = tlm_gap_event[0]
        assert tlm_gap_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            }
        ]
        # Check no discrepancy
        tlm_no_discrepancy_event = self.query_eboa.get_events(gauge_names = {"filter": "DISCREPANCY_CHANNEL_2_NOMINAL_MEMORY_OCCUPATION", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T00:00:00.00", "op": "=="}])
        assert len(tlm_no_discrepancy_event) == 0

        # Check gap event
        tlm_gap_events = self.query_eboa.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_CHANNEL_1_GAP", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T06:36:25.132008", "op": "=="}])

        assert len(tlm_gap_events) == 1
        tlm_gap_event = tlm_gap_events[0]

        assert tlm_gap_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            }
        ]

        # Check last gap event
        tlm_gap_events = self.query_eboa.get_events(gauge_names = {"filter": "NRT_MEMORY_OCCUPATION_CHANNEL_1_GAP", "op": "=="},
                                                gauge_systems = {"filter": "S2B", "op": "=="},
                                                sources = {"filter": "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001_DISCREPANCY_VERSION.EOF", "op": "=="},
                                                start_filters = [{"date": "2020-11-26T23:59:50.132000", "op": "=="}])

        assert len(tlm_gap_events) == 1
        tlm_gap_event = tlm_gap_events[0]

        assert tlm_gap_event.get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2B" 
            }
        ]
        

    def test_insert_tlm_req_with_plan_and_orbpre(self):
        filename = "S2B_OPER_MPL__NPPF__20201112T120000_20201130T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_MPL_ORBPRE_20201125T030111_20201205T030111_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_TLM__REQ_B_20201126T000000_20201127T000000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_tlm_req_b.ingestion_tlm_req_b", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # CHECK NOMINAL_MEMORY_OCCUPATION LINKS

        # Check planned_playback events
        nominal_memory_links = self.query_eboa.get_linking_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                    stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})
        planned_playback_events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}])

        assert len(nominal_memory_links["linking_events"]) == 31

        # Check nominal memory links to start planned playback events
        nominal_memory_links_at_start_planned_playback = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_AT_START", "op": "=="})

        assert len(nominal_memory_links_at_start_planned_playback["linking_events"]) == 29

        # Check nominal memory links to stop planned playback events
        nominal_memory_links_at_stop_planned_playback = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_AT_STOP", "op": "=="})

        assert len(nominal_memory_links_at_stop_planned_playback["linking_events"]) == 28

        # Check planned imaging events
        planned_imaging_events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}])
        
        nominal_memory_links_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                    stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "=="})

        assert len(nominal_memory_links_imaging["linking_events"]) == 54

        # Check nominal memory links to start planned imaging events
        nominal_memory_links_at_start_planned_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_AT_START", "op": "=="})

        assert len(nominal_memory_links_at_start_planned_imaging["linking_events"]) == 50

        # Check nominal memory links to stop planned imaging events
        nominal_memory_links_at_stop_planned_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                            stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                            link_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_AT_STOP", "op": "=="})

        assert len(nominal_memory_links_at_stop_planned_imaging["linking_events"]) == 52

        # Check planned cut imaging events
        planned_cut_imaging_events = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}])
        
        nominal_memory_links_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                    stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                    link_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})
        
        assert len(nominal_memory_links_cut_imaging["linking_events"]) == 54

        # Check nominal memory links to start planned cut imaging events
        nominal_memory_links_at_start_planned_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_AT_START", "op": "=="})

        assert len(nominal_memory_links_at_start_planned_cut_imaging["linking_events"]) == 50

        # Check nominal memory links to stop planned cut imaging events
        nominal_memory_links_at_stop_planned_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NOMINAL_MEMORY_OCCUPATION_AT_STOP", "op": "=="})

        assert len(nominal_memory_links_at_stop_planned_cut_imaging["linking_events"]) == 51

        # CHECK NRT_MEMORY_OCCUPATION LINKS

        # Check nrt memory links to planned playback events
        nrt_memory_links = self.query_eboa.get_linking_events(gauge_names = {"filter": "NRT_MEMORY_OCCUPATION", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                    stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})
        
        assert len(nrt_memory_links["linking_events"]) == 31

        # Check nrt memory links to start planned playback events
        nrt_memory_links_at_start_planned_playback = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NRT_MEMORY_OCCUPATION_AT_START", "op": "=="})

        assert len(nrt_memory_links_at_start_planned_playback["linking_events"]) == 1

        # Check nrt memory links to stop planned playback events
        nrt_memory_links_at_stop_planned_playback = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NRT_MEMORY_OCCUPATION_AT_STOP", "op": "=="})

        assert len(nrt_memory_links_at_stop_planned_playback["linking_events"]) == 1

        # Check nrt memory links to planned imaging events
        nrt_memory_links_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "NRT_MEMORY_OCCUPATION", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                    stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "=="})
        assert len(nrt_memory_links_imaging["linking_events"]) == 54

        # Check nrt memory links to start planned imaging events
        nrt_memory_links_at_start_planned_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NRT_MEMORY_OCCUPATION_AT_START", "op": "=="})

        assert len(nrt_memory_links_at_start_planned_imaging["linking_events"]) == 1

        # Check nrt memory links to stop planned imaging events
        nrt_memory_links_at_stop_planned_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                            stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                            link_names = {"filter": "NRT_MEMORY_OCCUPATION_AT_STOP", "op": "=="})

        assert len(nrt_memory_links_at_stop_planned_imaging["linking_events"]) == 1

        # Check nrt memory links to planned cut imaging events
        nrt_memory_links_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "NRT_MEMORY_OCCUPATION", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                    stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                    link_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})
        
        assert len(nrt_memory_links_cut_imaging["linking_events"]) == 54

        # Check nrt memory links to start planned cut imaging events
        nrt_memory_links_at_start_planned_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NRT_MEMORY_OCCUPATION_AT_START", "op": "=="})

        assert len(nrt_memory_links_at_start_planned_cut_imaging["linking_events"]) == 1

        # Check nrt memory links to stop planned cut imaging events
        nrt_memory_links_at_stop_planned_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "NRT_MEMORY_OCCUPATION_AT_STOP", "op": "=="})

        assert len(nrt_memory_links_at_stop_planned_cut_imaging["linking_events"]) == 1

        # CHECK LAST_REPLAYED_SCENE LINKS 

        # Check last replayed links to planned playback events
        last_replayed_links = self.query_eboa.get_linking_events(gauge_names = {"filter": "LAST_REPLAYED_SCENE", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                    stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})
        
        assert len(last_replayed_links["linking_events"]) == 31

        # Check last replayed links to start planned playback events
        last_replayed_links_at_start_planned_playback = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "LAST_REPLAYED_SCENE_AT_START", "op": "=="})

        assert len(last_replayed_links_at_start_planned_playback["linking_events"]) == 29

        # Check last replayed links to stop planned playback events
        last_replayed_links_at_stop_planned_playback = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "LAST_REPLAYED_SCENE_AT_STOP", "op": "=="})

        assert len(last_replayed_links_at_stop_planned_playback["linking_events"]) == 29

        # Check last replayed links to planned imaging events
        last_replayed_links_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "LAST_REPLAYED_SCENE", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                    stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                    link_names = {"filter": "PLANNED_IMAGING", "op": "=="})

        assert len(last_replayed_links_imaging["linking_events"]) == 54

        # Check last replayed links to start planned imaging events
        last_replayed_links_at_start_planned_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "LAST_REPLAYED_SCENE_AT_START", "op": "=="})

        assert len(last_replayed_links_at_start_planned_imaging["linking_events"]) == 24

        # Check last replayed links to stop planned imaging events
        last_replayed_links_at_stop_planned_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-27T00:00:00", "op": "<"}], 
                                                                            stop_filters = [{"date": "2020-11-26T00:00:00", "op": ">"}], 
                                                                            link_names = {"filter": "LAST_REPLAYED_SCENE_AT_STOP", "op": "=="})

        assert len(last_replayed_links_at_stop_planned_imaging["linking_events"]) == 15

        # Check last replayed links to planned cut imaging events
        last_replayed_links_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "LAST_REPLAYED_SCENE", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                    stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                    link_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})
        
        assert len(last_replayed_links_cut_imaging["linking_events"]) == 54

        # Check last replayed links to start planned cut imaging events
        last_replayed_links_at_start_planned_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "LAST_REPLAYED_SCENE_AT_START", "op": "=="})

        assert len(last_replayed_links_at_start_planned_cut_imaging["linking_events"]) == 24

        # Check last replayed links to stop planned cut imaging events
        last_replayed_links_at_stop_planned_cut_imaging = self.query_eboa.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="},
                                                                            gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                            value_filters = [{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD", "SAD"]}}],
                                                                            start_filters = [{"date": "2020-11-26T00:00:00", "op": ">="}], 
                                                                            stop_filters = [{"date": "2020-11-27T00:00:00", "op": "<="}], 
                                                                            link_names = {"filter": "LAST_REPLAYED_SCENE_AT_STOP", "op": "=="})

        assert len(last_replayed_links_at_stop_planned_cut_imaging["linking_events"]) == 15