"""
Automated tests for the ingestion of the REP_OPDAM files

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

class TestDam(unittest.TestCase):
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

    def test_rep_dam_only(self):

        filename = "S2__OPER_REP_OPDAM2_PDMC_20180721T110502_ONLY.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dam.ingestion_dam", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T07:22:04", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:05:02", "op": "=="}],
                                              processors = {"filter": "ingestion_dam.py", "op": "like"},
                                              names = {"filter": "S2__OPER_REP_OPDAM2_PDMC_20180721T110502_ONLY.EOF", "op": "like"})

        assert len(sources) == 1

        #Check definite datatake
        definite_datatakes = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "DATATAKE"},
                                                     explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"})

        assert definite_datatakes[0].get_structured_values() == [
            {'type': 'text',
             'name': 'datatake_identifier',
             'value': 'GS2A_20180721T083601_016077_N02.06'
            }]

        ### Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight
        # # Check definite_cataloging_times
        # definite_cataloging_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "CATALOGING_TIME"},
        #                                                      explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_SGS__20180721T103208_S20180721T072204_D01_N02.06"})

        # assert definite_cataloging_times[0].get_structured_values() == [
        #     {
        #         "value": "2018-07-21T11:03:17.080882",
        #         "type": "timestamp",
        #         "name": "cataloging_time"
        #     }]
        ### End Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight

        # Check definite_baseline
        definite_baseline = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "BASELINE"},
                                                                    explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06"})

        assert definite_baseline[0].get_structured_values() == [
            {
                "value": "N02.06",
                "type": "text",
                "name": "baseline"
            }]

        #Check baseline
        baseline = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "BASELINE"})

        ### Corrections made on 2019/11/27 to avoid inserting information regarding granules
        assert len(baseline) == 2

        #Check datatakes
        datatakes = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "DATATAKE"})

        assert len(datatakes) == 2

        #Check cataloguin time
        cataloging_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "CATALOGING_TIME"})

        assert len(cataloging_times) == 2

        # Check data sizes
        datatakes = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "DATATAKE"})

        assert len(datatakes) == 2
        ### End Corrections made on 2019/11/27 to avoid inserting information regarding granules

        # Check datastrip_sensing_explicit_ref
        datastrip_sensing_er = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "S2A_OPER_MSI_L0__DS_MPS__20180721T103920_S20180721T085229_N02.06", "op": "like"},
                                                                 groups =  {"op": "like", "filter": "L0_DS"})

        assert len(datastrip_sensing_er) == 1

        ### Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight
        # # Check granule_explicit_ref
        # granule_er = self.query_eboa.get_explicit_refs(groups = {"op": "like", "filter": "L0_GR"})

        # assert len(granule_er) == 2
        ### End Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight

        # Check tile_explicit_ref
        tile_er = self.query_eboa.get_explicit_refs(groups = {"op": "like", "filter": "L2A_TL"})

        assert len(tile_er) == 1

    def test_rep_dam_with_rep_arc(self):

        filename = "S2__OPER_REP_ARC____EPA__20180721T110140_N0206.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_REP_OPDAM2_PDMC_20180721T110502_WITH_REP_ARC.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_dam.ingestion_dam", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2018-07-21T07:22:04", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-21T08:54:14", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T11:05:02", "op": "=="}],
                                              processors = {"filter": "ingestion_dam.py", "op": "like"},
                                              names = {"filter": "S2__OPER_REP_OPDAM2_PDMC_20180721T110502_WITH_REP_ARC.EOF", "op": "like"})

        assert len(sources) == 1

        ### Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight
        # # Check definite_cataloging_times
        # definite_cataloging_times = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "CATALOGING_TIME"},
        #                                                      explicit_refs = {"op": "like", "filter": "S2A_OPER_MSI_L0__GR_MPS__20180721T103920_S20180721T085229_D01_N02.06"})

        # assert definite_cataloging_times[0].get_structured_values() == [
        #     {
        #         "value": "2018-07-21T11:02:36.601190",
        #         "type": "timestamp",
        #         "name": "cataloging_time"
        #     }]

        # # Check granule_explicit_ref
        # granule_er = self.query_eboa.get_explicit_refs(groups = {"op": "like", "filter": "L0_GR"})

        # assert len(granule_er) == 0
        ### End Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight
