"""
Automated tests for the ingestion of the REP_OPLTA files

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

    def test_rep_lta(self):

        filename = "S2__OPER_REP_OPLTA__EPA__20180721T130015_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_lta.ingestion_lta", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T01:00:02", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-21T13:00:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T13:00:15", "op": "=="}],
                                              processors = {"filter": "ingestion_lta.py", "op": "like"},
                                              names = {"filter": "S2__OPER_REP_OPLTA__EPA__20180721T130015_RIPPED.EOF", "op": "like"})

        assert len(sources) == 1

        #Check definite archiving_time
        definite_archiving_time = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "LONG_TERM_ARCHIVING_TIME"},
                                                     explicit_refs = {"op": "like", "filter": "S2B_OPER_MSI_L1C_TC_SGS__20171017T181225_A003211_T23VNK_N02.05"})

        assert definite_archiving_time[0].get_structured_values() == [
            {'type': 'timestamp',
             'name': 'long_term_archiving_time',
             'value': '2018-07-21T01:00:10'
            }]

        #Check archiving_times
        archiving_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "LONG_TERM_ARCHIVING_TIME"})

        assert len(archiving_times) == 3
