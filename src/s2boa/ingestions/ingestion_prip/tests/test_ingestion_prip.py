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

        sources = self.query_eboa.get_sources()

        assert len(sources) == 1

        sources = self.query_eboa.get_sources(validity_start_filters = [{"date": "2021-02-22T11:50:02", "op": "=="}],
                                              validity_stop_filters = [{"date": "2021-02-22T17:50:01", "op": "=="}],
                                              generation_time_filters = [{"date": "2021-02-22T18:00:03", "op": "=="}],
                                              processors = {"filter": "ingestion_prip.py", "op": "like"},
                                              names = {"filter": "S2__OPER_REP_OPPRIP_PDMC_20210222T180003_V20210222T115002_20210222T175001.test", "op": "like"})

        assert len(sources) == 1

        # Check annotations
        prip_annotations = self.query_eboa.get_annotations()

        assert len(prip_annotations) == 15

        prip_annotation_archiving_time = self.query_eboa.get_annotations(annotation_cnf_names = {"op": "like", "filter": "PRIP_ARCHIVING_TIME"},
                                                     explicit_refs = {"op": "like", "filter": "S2B_OPER_GIP_R2EQOG_MPC__20210222T083100_V20210223T233000_21000101T000000_B05"})

        assert len(prip_annotation_archiving_time) == 1
        
        assert prip_annotation_archiving_time[0].get_structured_values() == [
            {'type': 'timestamp',
             'name': 'prip_archiving_time',
             'value': '2021-02-22T15:27:48'
            }]

        # Check explicit references
        prip_ds_explicit_refs = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%_DS_%", "op": "like"})
        
        assert len(prip_ds_explicit_refs) == 6

        # prip_granules_explicit_refs = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%_GR_%", "op": "like"})
        
        # assert len(prip_granules_explicit_refs) == 2

        prip_tiles_explicit_refs = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%_TL_%", "op": "like"})
        
        assert len(prip_tiles_explicit_refs) == 1

        prip_tcs_explicit_refs = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%_TC_%", "op": "like"})
        
        assert len(prip_tcs_explicit_refs) == 1

        prip_aux_explicit_refs = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%AUX%", "op": "like"})
        
        assert len(prip_aux_explicit_refs) == 3

        prip_hktms_explicit_refs = self.query_eboa.get_explicit_refs(explicit_refs = {"filter": "%HKTM%", "op": "like"})
        
        assert len(prip_hktms_explicit_refs) == 1


        # Check linked explicit references
        prip_linked_explicit_refs = self.query_eboa.get_linking_explicit_refs(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_TL_VGS1_20210318T070626_A029960_T47VPJ_N02.09", "op": "=="})

        assert len(prip_linked_explicit_refs["linking_explicit_refs"]) == 1

        assert prip_linked_explicit_refs["linking_explicit_refs"][0].explicit_ref == "S2B_OPER_MSI_L1C_DS_VGS4_20210318T080123_S20210318T061751_N02.09"

        prip_linked_explicit_refs = self.query_eboa.get_linking_explicit_refs(explicit_refs = {"filter": "S2A_OPER_MSI_L1C_TC_VGS4_20210319T053620_A029973_T50PMU_N02.09", "op": "=="})

        assert len(prip_linked_explicit_refs["linking_explicit_refs"]) == 1

        assert prip_linked_explicit_refs["linking_explicit_refs"][0].explicit_ref == "S2B_OPER_MSI_L1C_DS_VGS2_20210219T052736_S20210219T043615_N02.09"

        # prip_linked_explicit_refs = self.query_eboa.get_linking_explicit_refs(explicit_refs = {"filter": "S2B_OPER_MSI_L0__DS_VGS2_20210222T112736_S20210222T093615_N02.09", "op": "=="})

        # assert len(prip_linked_explicit_refs["linking_explicit_refs"]) == 1

        # assert prip_linked_explicit_refs["linking_explicit_refs"][0].explicit_ref == "S2B_OPER_MSI_L0__GR_VGS2_20210222T112736_S20210222T093828_D02_N02.09"
        
 
        
