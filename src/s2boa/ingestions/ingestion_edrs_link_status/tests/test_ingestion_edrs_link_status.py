"""
Automated tests for the ingestion of the EDR Report files

Written by DEIMOS Space S.L. (jubv)

module ingestions
"""
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

    def test_insert_edr_report(self):
        filename = "EDR_OPER_SER_SR1_OA_PDMC_20200719T012002_V20200718T235713_20200719T001700"

        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_edrs_link_status.ingestion_edrs_link_status", file_path, "2018-01-01T00:00:00")
        
        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 2

        # Check that the validity period of the input is correctly taken
        source_period = self.session.query(Source).filter(Source.validity_start == "2020-07-18T23:57:13",
                                                          Source.validity_stop == "2020-07-19T00:17:00").all()

        assert len(source_period) == 1

        #Check that the name of the input file is correctly taken
        source_name = self.session.query(Source).filter(Source.name == "EDR_OPER_SER_SR1_OA_PDMC_20200719T012002_V20200718T235713_20200719T001700").all()

        assert len(source_name) == 1

        #Check that the generation date of the input file is correctly taken
        source_gen_date = self.session.query(Source).filter(Source.generation_time == "UTC=2020-07-19T01:20:02").all()

        assert len(source_gen_date) == 1

        # Check that the Gauge name is correctly taken
        gauge_name = self.session.query(Event).join(Gauge).filter(Gauge.name.like("LINK_EXECUTION_STATUS_DCSU_%")).all()

        assert len(gauge_name) == 2

        # Check that the Gauge system is correctly taken
        gauge_system = self.session.query(Event).join(Gauge).filter(Gauge.system == "EDRS-A").all()

        assert len(gauge_system) == 2

        # Check that the Dim Signature is correctly taken
        definite_dim_signature = self.session.query(DimSignature).filter(DimSignature.dim_signature == "LINK_EXECUTION_STATUS_S2A").all()

        assert len(definite_dim_signature) == 1

        # Check that the key is correctly taken
        definite_key = self.session.query(EventKey).filter(EventKey.event_key.like("LINK_EXECUTION_STATUS-L20200519095434225000125-%")).all()

        assert len(definite_key) == 2

        # Check LINK_EXECUTION_STATUS_DCSU events
        definite_link_execution_status_dcsu_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "LINK_EXECUTION_STATUS_DCSU_02",
                                                                                   Event.start == "2020-07-18T23:57:13",
                                                                                   Event.stop == "2020-07-19T00:17:00").all()

        assert definite_link_execution_status_dcsu_event1[0].get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },
            {
                "name": "session_id",
                "type": "text",
                "value": "L20200519095434225000125"
            },
            {
                "name": "status",
                "type": "text",
                "value": "FAILED"
            },
            {
                "name": "characterized_status",
                "type": "text",
                "value": "NOK"
            },
            {
                "name": "dcsu_id",
                "type": "text",
                "value": "02"
            },
            {
                "name": "link_session_fer",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "number_of_delivered_cadu",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "number_of_missing_cadu",
                "type": "double",
                "value": "0.0"
            }
        ]

        definite_link_execution_status_dcsu_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "LINK_EXECUTION_STATUS_DCSU_04",
                                                                                   Event.start == "2020-07-18T23:57:13",
                                                                                   Event.stop == "2020-07-19T00:17:00").all()

        assert definite_link_execution_status_dcsu_event2[0].get_structured_values() == [
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },
            {
                "name": "session_id",
                "type": "text",
                "value": "L20200519095434225000125"
            },
            {
                "name": "status",
                "type": "text",
                "value": "FAILED"
            },
            {
                "name": "characterized_status",
                "type": "text",
                "value": "NOK"
            },
            {
                "name": "dcsu_id",
                "type": "text",
                "value": "04"
            },
            {
                "name": "link_session_fer",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "number_of_delivered_cadu",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "number_of_missing_cadu",
                "type": "double",
                "value": "0.0"
            }
        ]

        # Check that the Explicit is correctly taken
        explicit_refs = self.session.query(ExplicitRef).all()

        assert len(explicit_refs) == 1

        definite_explicit_ref = self.session.query(ExplicitRef).join(ExplicitRefGrp).filter(ExplicitRef.explicit_ref == "L20200519095434225000125",
                                                                                    ExplicitRefGrp.name == "EDRS_LINK_SESSION_IDs").all()

        assert len(definite_explicit_ref) == 1