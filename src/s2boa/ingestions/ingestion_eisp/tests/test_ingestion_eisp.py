"""
Automated tests for the ingestion of the REP_PASS_E_VGS files

Written by DEIMOS Space S.L. (dibb)

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

class TestEispIngestion(unittest.TestCase):
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

    def test_insert_rep_pass_no_gaps(self):
        filename = "S2A_OPER_REP_PASS_E_VGS2_20210226T182335_V20210226T180118_20210226T180928.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 17

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS_CH1").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "S2A_20210226180111029682",
                "type": "text",
                "name": "session_id"
            },
            {
                "value": "29682.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "SGS_",
                "type": "text",
                "name": "reception_station"
            },
            {
                "value": "COMPLETE",
                "type": "text",
                "name": "isp_status"
            },
            {
                "value": "COMPLETE",
                "type": "text",
                "name": "acquisition_status"
            }
        ]

        # Check ISP_VALIDITY events
        isp_validities = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY").all()

        assert len(isp_validities) == 3

        # Check specific ISP_VALIDITY
        specific_isp_validity = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T15:08:54.264729",
                                                                                 Event.stop == "2021-02-26T15:17:44.607184").all()

        assert len(specific_isp_validity) == 1

        # Check specific ISP_VALIDITY
        specific_isp_validity = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T15:22:13.855720",
                                                                                 Event.stop == "2021-02-26T15:22:53.541439").all()

        assert len(specific_isp_validity) == 1

        # Check specific ISP_VALIDITY
        specific_isp_validity = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T16:32:24.848297",
                                                                                 Event.stop == "2021-02-26T16:35:32.452882").all()

        assert len(specific_isp_validity) == 1

        assert specific_isp_validity[0].get_structured_values() == [
            {
                "value": "COMPLETE",
                "name": "status",
                "type": "text"
            },
            {
                "value": "29682.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "SGS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "4.0",
                "name": "vcid",
                "type": "double"
            },
            {
                "value": "NOMINAL",
                "name": "playback_type",
                "type": "text"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "MISSING"
            }
        ]

        # Check RAW_ISP_VALIDITY events
        raw_isp_validities = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY").all()

        assert len(raw_isp_validities) == 1

        # Check specific RAW_ISP_VALIDITY
        specific_raw_isp_validity = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T15:08:54.264729",
                                                                                 Event.stop == "2021-02-26T16:35:32.452882").all()

        assert len(specific_raw_isp_validity) == 1

        assert specific_raw_isp_validity[0].get_structured_values() == [
            {
                "value": "COMPLETE",
                "name": "status",
                "type": "text"
            },
            {
                "value": "29682.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "SGS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "4.0",
                "name": "vcid",
                "type": "double"
            },
            {
                "value": "NOMINAL",
                "name": "playback_type",
                "type": "text"
            },
            {
                "value": "1360800.0",
                "name": "num_packets",
                "type": "double"
            },
            {
                "value": "12105158.0",
                "name": "num_frames",
                "type": "double"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "MISSING"
            },
            {
                "value": "1360800.0",
                "name": "expected_num_packets",
                "type": "double"
            },
            {
                "value": "0.0",
                "name": "diff_expected_received",
                "type": "double"
            },
            {
                "name": "packet_status",
                "type": "text",
                "value": "OK"
            }
        ]

        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(isp_completeness_events) == 3
        
        # Check PLAYBACK_VALIDITY_3 events
        playback_validity_3s = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_3").all()

        assert len(playback_validity_3s) == 1

        # Check specific PLAYBACK_VALIDITY_3
        specific_playback_validity_3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_3",
                                                                                 Event.start == "2021-02-26T18:08:43.072530",
                                                                                 Event.stop == "2021-02-26T18:09:23.609233").all()

        assert len(specific_playback_validity_3) == 1

        assert specific_playback_validity_3[0].get_structured_values() == [
            {
                "value": "29682.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "SGS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "3.0",
                "name": "vcid",
                "type": "double"
            },
            {
                "value": "HKTM",
                "name": "playback_type",
                "type": "text"
            },
            {
                "value": "COMPLETE",
                "name": "status",
                "type": "text"
            }
        ]


        # Check PLAYBACK_VALIDITY_4 events
        playback_validity_4s = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_4").all()

        assert len(playback_validity_4s) == 1

        # Check specific PLAYBACK_VALIDITY_4
        specific_playback_validity_4 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_4",
                                                                                 Event.start == "2021-02-26T18:01:23.007471",
                                                                                 Event.stop == "2021-02-26T18:08:42.798204").all()

        assert len(specific_playback_validity_4) == 1

        assert specific_playback_validity_4[0].get_structured_values() == [
            {
                "value": "29682.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "SGS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "4.0",
                "name": "vcid",
                "type": "double"
            },
            {
                "value": "NOMINAL",
                "name": "playback_type",
                "type": "text"
            },
            {
                "value": "COMPLETE",
                "name": "status",
                "type": "text"
            }
        ]

        # Check HKTM_DISTRIBUTION events
        hktm_distributions = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_HKTM_DISTRIBUTION_STATUS_CHANNEL_1").all()

        assert len(hktm_distributions) == 1

        # Check specific HKTM_DISTRIBUTION
        specific_hktm_distribution = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_HKTM_DISTRIBUTION_STATUS_CHANNEL_1",
                                                                                 Event.start == "2021-02-26T18:01:18.514698",
                                                                                 Event.stop == "2021-02-26T18:09:28.670270").all()

        assert len(specific_hktm_distribution) == 1

        assert specific_hktm_distribution[0].get_structured_values() == [
            {
                "value": "DELIVERED",
                "name": "status",
                "type": "text"
            },
            {
                "value": "29682.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "SGS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "OK",
                "name": "completeness_status",
                "type": "text"
            },
            {
                "value": "18503.0",
                "name": "number_of_received_transfer_frames",
                "type": "double"
            },
            {
                "value": "18503.0",
                "name": "number_of_distributed_transfer_frames",
                "type": "double"
            },
            {
                "value": "0.0",
                "name": "completeness_difference",
                "type": "double"
            }
        ]


        # Check ISP_DISTRIBUTION events
        isp_distributions = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_1").all()

        assert len(isp_distributions) == 1

        # Check specific ISP_DISTRIBUTION
        specific_isp_distribution = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_1",
                                                                                 Event.start == "2021-02-26T18:01:18.514698",
                                                                                 Event.stop == "2021-02-26T18:09:28.670270").all()

        assert len(specific_isp_distribution) == 1

        assert specific_isp_distribution[0].get_structured_values() == [
            {
                "value": "DELIVERED",
                "name": "status",
                "type": "text"
            },
            {
                "value": "29682.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "SGS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "OK",
                "name": "completeness_status",
                "type": "text"
            },
            {
                "value": "1360800.0",
                "name": "number_of_received_isps",
                "type": "double"
            },
            {
                "value": "1360800.0",
                "name": "number_of_distributed_isps",
                "type": "double"
            },
            {
                "value": "0.0",
                "name": "completeness_difference",
                "type": "double"
            }
        ]

