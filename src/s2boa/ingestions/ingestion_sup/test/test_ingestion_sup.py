"""
Automated tests for the ingestion of the REP_OPPRIP files

Written by DEIMOS Space S.L. (miaf)

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

class TestOpprip(unittest.TestCase):
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

    def test_insert_repsup_with_unknown_validity_stop(self):

        filename = "S2A_OPER_REP__SUP___20201128T134025_99999999T999999_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_sup.ingestion_sup", file_path, "2021-02-23T00:00:00")
       

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-11-28T13:40:25", "op": "=="}],
                                              validity_stop_filters = [{"date": "9999-12-31T23:59:59.999999", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-11-28T18:07:58", "op": "=="}],
                                              processors = {"filter": "ingestion_sup.py", "op": "like"},
                                              names = {"filter": "S2A_OPER_REP__SUP___20201128T134025_99999999T999999_0001.EOF", "op": "like"})

        assert len(sources) == 1

        # Check events
        sup_events = self.query_eboa.get_events()

        assert len(sup_events) == 1

        sup_event = self.query_eboa.get_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="},
                                                    gauge_systems = {"filter": "S2A", "op": "=="},
                                                    sources = {"filter": "S2A_OPER_REP__SUP___20201128T134025_99999999T999999_0001.EOF", "op": "=="},
                                                    start_filters = [{"date": "2020-11-28T13:40:25", "op": "=="}])
        

        assert len(sup_event) == 1

        assert sup_events[0].get_structured_values() == [
                    {"name": "satellite",
                    "type": "text",
                    "value": "S2A"
                    },
                    {"name": "subsystem",
                    "type": "text",
                    "value": "OCP"
                    },
                    {"name": "comment",
                    "type": "text",
                    "value": "Outage due to GS2_OCP-04 TAPCO RESET"
                    },
                    {"name": "start_orbit",
                    "type": "double",
                    "value": "28392.0"
                    }]
    
    # Check if the previously inserted event is updated
    def test_insert_repsups_with_same_key(self):
        filename = "S2A_OPER_REP__SUP___20201128T134025_99999999T999999_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_sup.ingestion_sup", file_path, "2021-02-23T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP__SUP___20201128T134025_20201128T134611_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_sup.ingestion_sup", file_path, "2021-02-23T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        sources = self.query_eboa.get_sources()

        assert len(sources) == 2

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2020-11-28T13:40:25", "op": "=="}],
                                              validity_stop_filters = [{"date": "2020-11-28T13:46:11", "op": "=="}],
                                              generation_time_filters = [{"date": "2020-11-28T18:10:54", "op": "=="}],
                                              processors = {"filter": "ingestion_sup.py", "op": "like"},
                                              names = {"filter": "S2A_OPER_REP__SUP___20201128T134025_20201128T134611_0001.EOF", "op": "like"})

        assert len(sources) == 1

        # Check that the event has been updated
        sup_events = self.query_eboa.get_events()

        assert len(sup_events) == 1     # Only one event remaining

        sup_event = self.query_eboa.get_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="},
                                                    gauge_systems = {"filter": "S2A", "op": "=="},
                                                    sources = {"filter": "S2A_OPER_REP__SUP___20201128T134025_20201128T134611_0001.EOF", "op": "=="},
                                                    start_filters = [{"date": "2020-11-28T13:40:25", "op": "=="}])
        

        assert len(sup_event) == 1

        assert sup_events[0].get_structured_values() == [
                    {"name": "satellite",
                    "type": "text",
                    "value": "S2A"
                    },
                    {"name": "subsystem",
                    "type": "text",
                    "value": "OCP"
                    },
                    {"name": "comment",
                    "type": "text",
                    "value": "Outage due to GS2_OCP-04 TAPCO RESET Outage due to GS2_OCP-04 TAPCO RESET"
                    },
                    {"name": "start_orbit",
                    "type": "double",
                    "value": "28392.0"
                    }, 
                    {"name": "stop_orbit",
                    "type": "double",
                    "value": "28392.0"
                    }]

    # Check links
    def test_insert_repsups_with_links(self):
        
        self.query_eboa.clear_db()
        
        filename = "S2B_OPER_MPL__NPPF__20201112T120000_20201130T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        

        filename = "S2B_OPER_MPL_ORBPRE_20201125T030111_20201205T030111_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2B_OPER_REP__SUP___20201126T130000_20201127T103000_0001.test"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_sup.ingestion_sup", file_path, "2021-02-23T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        sources = self.query_eboa.get_sources()

        assert len(sources) == 6

        # Number of rep_sup events
        sup_event = self.query_eboa.get_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="},
                                                    gauge_systems = {"filter": "S2B", "op": "=="},
                                                    sources = {"filter": "S2B_OPER_REP__SUP___20201126T130000_20201127T103000_0001.test", "op": "=="})
        
        assert len(sup_event) == 4

        #Number of linking events
        xband_linking_events = self.query_eboa.get_linking_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T22:45:00", "op": "=="}], 
                                                                    stop_filters = [{"date": "2020-11-26T23:00:00", "op": "=="}], 
                                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})
        
        len(xband_linking_events["linking_events"]) == 2

        ocp_linking_events = self.query_eboa.get_linking_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T22:45:00", "op": "=="}], 
                                                                    stop_filters = [{"date": "2020-11-26T23:00:00", "op": "=="}], 
                                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})
        
        len(xband_linking_events["linking_events"]) == 2

        msi_linking_events = self.query_eboa.get_linking_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T15:00:00", "op": "=="}], 
                                                                    stop_filters = [{"date": "2020-11-26T16:30:00", "op": "=="}], 
                                                                    link_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})
        
        len(xband_linking_events["linking_events"]) == 5

        mmfu_linking_events = self.query_eboa.get_linking_events(gauge_names = {"filter": "SYSTEM_UNAVAILABILITY", "op": "=="}, 
                                                                    gauge_systems = {"filter": "S2B", "op": "=="}, 
                                                                    start_filters = [{"date": "2020-11-26T19:00:00", "op": "=="}], 
                                                                    stop_filters = [{"date": "2020-11-26T20:30:00", "op": "=="}], 
                                                                    link_names = {"filter": "PLANNED_CUT_IMAGING", "op": "=="})
        
        len(xband_linking_events["linking_events"]) == 4

        

   

        








    

