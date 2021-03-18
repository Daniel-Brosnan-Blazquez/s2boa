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

    def test_insert_opprip(self):

        filename = "S2__OPER_REP_OPPRIP_PDMC_20210222T180003_V20210222T115002_20210222T175001.test"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

   
        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_prip.ingestion_prip", file_path, "2021-02-23T00:00:00")
       
        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        """
        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2021-02-22T17:50:01", "op": "=="}],
                                              validity_stop_filters = [{"date": "2021-02-22T23:50:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2021-02-23T00:00:02", "op": "=="}],
                                              processors = {"filter": "ingestion_prip.py", "op": "like"},
                                              names = {"filter": "S2__OPER_REP_OPPRIP_PDMC_20210223T000002_V20210222T175001_20210222T235001.EOF", "op": "like"})

        assert len(sources) == 1

        """