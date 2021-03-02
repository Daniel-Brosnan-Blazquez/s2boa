"""
Automated tests for the ingestion of the REP_PASS_2|5 files

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

class TestDfepIngestion(unittest.TestCase):
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

    def test_insert_rep_pass(self):
        filename = "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 14

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39").all()

        assert len(sources) == 2

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "16078.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
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

        # Check specific ISP_VALIDITY
        specific_isp_validity1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(specific_isp_validity1) == 1

        # Check ISP_VALIDITY events
        isp_validities = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY").all()

        assert len(isp_validities) == 1

        # Check specific ISP_VALIDITY
        specific_isp_validity1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(specific_isp_validity1) == 1

        assert specific_isp_validity1[0].get_structured_values() == [
            {
                "value": "COMPLETE",
                "name": "status",
                "type": "text"
            },
            {
                "value": "16078.0",
                "name": "downlink_orbit",
                "type": "double"
            },
            {
                "value": "S2A",
                "name": "satellite",
                "type": "text"
            },
            {
                "value": "MPS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "NOMINAL",
                "name": "playback_type",
                "type": "text"
            },
            {
                "value": "NO_MATCHED_PLANNED_IMAGING",
                "name": "matching_plan_status",
                "type": "text"
            },
            {
                "value": "-1.0",
                "name": "sensing_orbit",
                "type": "double"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(isp_completeness_events) == 2

        # Check specific ISP_VALIDITY
        isp_completeness_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(isp_completeness_event1) == 1

        assert isp_completeness_event1[0].get_structured_values() == [
            {
                "value": "RECEIVED",
                "type": "text",
                "name": "status"
            },
            {
                "value": "16078.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
                "type": "text",
                "name": "reception_station"
            },
            {
                "value": "NOMINAL",
                "type": "text",
                "name": "playback_type"
            },
            {
                "value": "-1.0",
                "type": "double",
                "name": "sensing_orbit"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        # Check specific ISP_VALIDITY
        isp_completeness_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(isp_completeness_event2) == 1

        # Check PLAYBACK_VALIDITY events
        playback_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_%")).all()

        assert len(playback_validity_events) == 3

        # Check specific PLAYBACK_VALIDITY
        playback_validity_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_4",
                                                                                 Event.start == "2018-07-21T10:35:33.728601",
                                                                                 Event.stop == "2018-07-21T10:37:14.719834").all()

        assert len(playback_validity_event1) == 1

        assert playback_validity_event1[0].get_structured_values() == [
            {
                "value": "COMPLETE",
                "type": "text",
                "name": "status"
            },
            {
                "value": "16078.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
                "type": "text",
                "name": "reception_station"
            },
            {
                "value": "1.0",
                "type": "double",
                "name": "channel"
            },
            {
                "value": "4.0",
                "type": "double",
                "name": "vcid"
            },
            {
                "value": "NOMINAL",
                "type": "text",
                "name": "playback_type"
            },
            {
                "value": "NO_MATCHED_PLANNED_PLAYBACK",
                "type": "text",
                "name": "matching_plan_status"
            }
        ]

        playback_validity_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_20",
                                                                                 Event.start == "2018-07-21T10:35:33.760977",
                                                                                 Event.stop == "2018-07-21T10:37:14.753003").all()

        assert len(playback_validity_event2) == 1

        playback_validity_event3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_2",
                                                                                 Event.start == "2018-07-21T10:37:20.858708",
                                                                                 Event.stop == "2018-07-21T10:37:26.355940").all()

        assert len(playback_validity_event3) == 1

        # Check PLANNED_PLAYBACK_COMPLETENESS_CHANNEL events
        playback_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK_COMPLETENESS_CHANNEL%")).all()

        assert len(playback_completeness_events) == 3

        # Check specific PLANNED_PLAYBACK_COMPLETENESS_CHANNEL
        playback_completeness_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T10:35:33.728601",
                                                                                 Event.stop == "2018-07-21T10:37:14.719834").all()

        assert len(playback_completeness_event1) == 1

        assert playback_completeness_event1[0].get_structured_values() == [
            {
                "type": "text",
                "value": "RECEIVED",
                "name": "status"
            },
            {
                "type": "double",
                "value": "16078.0",
                "name": "downlink_orbit"
            },
            {
                "type": "text",
                "value": "S2A",
                "name": "satellite"
            },
            {
                "type": "text",
                "value": "MPS_",
                "name": "reception_station"
            },
            {
                "type": "text",
                "value": "NOMINAL",
                "name": "playback_type"
            }
        ]

        playback_completeness_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T10:35:33.760977",
                                                                                 Event.stop == "2018-07-21T10:37:14.753003").all()

        assert len(playback_completeness_event2) == 1

        playback_completeness_event3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T10:37:20.858708",
                                                                                 Event.stop == "2018-07-21T10:37:26.355940").all()

        assert len(playback_completeness_event3) == 1

        # Check RAW_ISP_VALIDITY events
        raw_isp_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY").all()

        assert len(raw_isp_validity_events) == 1

        # Check specific RAW_ISP_VALIDITY
        raw_isp_validity_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:14.618646").all()

        assert len(raw_isp_validity_event1) == 1

        assert raw_isp_validity_event1[0].get_structured_values() == [
            {
                "name": "status",
                "type": "text",
                "value": "COMPLETE"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "MPS_"
            },
            {
                "name": "num_packets",
                "type": "double",
                "value": "388800.0"
            },
            {
                "name": "num_frames",
                "type": "double",
                "value": "1729309.0"
            },
            {
                "name": "expected_num_packets",
                "type": "double",
                "value": "388800.0"
            },
            {
                "name": "diff_expected_received",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "packet_status",
                "type": "text",
                "value": "OK"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        # Check DISTRIBUTION_STATUS events
        distribution_status_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_%_DISTRIBUTION_STATUS%")).all()

        assert len(distribution_status_events) == 2

        # Check specific DISTRIBUTION_STATUS event
        distribution_status_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T10:35:33.728601",
                                                                                 Event.stop == "2018-07-21T10:37:26.355940").all()

        assert len(distribution_status_event1) == 1

        assert distribution_status_event1[0].get_structured_values() == [
            {
                "name": "status",
                "type": "text",
                "value": "DELIVERED"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "MPS_"
            },
            {
                "name": "channel",
                "type": "double",
                "value": "1.0"
            },
            {
                "name": "completeness_status",
                "type": "text",
                "value": "OK"
            },
            {
                "name": "number_of_received_isps",
                "type": "double",
                "value": "194400.0"
            },
            {
                "name": "number_of_distributed_isps",
                "type": "double",
                "value": "194400.0"
            },
            {
                "name": "completeness_difference",
                "type": "double",
                "value": "0.0"
            }
        ]

        distribution_status_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T10:35:33.728601",
                                                                                 Event.stop == "2018-07-21T10:37:26.355940").all()

        assert len(distribution_status_event2) == 1

        assert distribution_status_event2[0].get_structured_values() == [
            {
                "name": "status",
                "type": "text",
                "value": "DELIVERED"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "MPS_"
            },
            {
                "name": "channel",
                "type": "double",
                "value": "2.0"
            },
            {
                "name": "completeness_status",
                "type": "text",
                "value": "OK"
            },
            {
                "name": "number_of_received_isps",
                "type": "double",
                "value": "2087228.0"
            },
            {
                "name": "number_of_distributed_isps",
                "type": "double",
                "value": "2087228.0"
            },
            {
                "name": "completeness_difference",
                "type": "double",
                "value": "0.0"
            }
        ]

        # Check DFEP_ACQUISITION_VALIDITY events
        dfep_acquisition_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name == "DFEP_ACQUISITION_VALIDITY").all()

        assert len(dfep_acquisition_validity_events) == 1

        # Check specific DFEP_ACQUISITION_VALIDITY event
        dfep_acquisition_validity_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "DFEP_ACQUISITION_VALIDITY",
                                                                                 Event.start == "2018-07-21T10:35:27",
                                                                                 Event.stop == "2018-07-21T10:37:39").all()

        assert len(dfep_acquisition_validity_event1) == 1

        assert dfep_acquisition_validity_event1[0].get_structured_values() == [
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "MPS_"
            }
        ]

    def test_insert_rep_pass_with_msi_gaps(self):
        filename = "S2A_REP_PASS_CONTAINING_MSI_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 19

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39").all()

        assert len(sources) == 2

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "16078.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
                "type": "text",
                "name": "reception_station"
            },
            {
                "value": "INCOMPLETE",
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

        assert len(isp_validities) == 1

        # Check specific ISP_VALIDITY
        specific_isp_validity1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(specific_isp_validity1) == 1

        assert specific_isp_validity1[0].get_structured_values() == [
            {
                "name": "status",
                "value": "INCOMPLETE",
                "type": "text"
            },
            {
                "name": "downlink_orbit",
                "value": "16078.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2A",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "MPS_",
                "type": "text"
            },
            {
                "name": "playback_type",
                "value": "NOMINAL",
                "type": "text"
            },
            {
                "name": "matching_plan_status",
                "value": "NO_MATCHED_PLANNED_IMAGING",
                "type": "text"
            },
            {
                "name": "sensing_orbit",
                "value": "-1.0",
                "type": "double"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(isp_completeness_events) == 2

        # Check specific ISP_VALIDITY
        isp_completeness_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(isp_completeness_event1) == 1

        assert isp_completeness_event1[0].get_structured_values() == [
            {
                "name": "status",
                "value": "INCOMPLETE",
                "type": "text"
            },
            {
                "name": "downlink_orbit",
                "value": "16078.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2A",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "MPS_",
                "type": "text"
            },
            {
                "name": "playback_type",
                "value": "NOMINAL",
                "type": "text"
            },
            {
                "name": "sensing_orbit",
                "value": "-1.0",
                "type": "double"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        # Check specific ISP_VALIDITY
        isp_completeness_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(isp_completeness_event2) == 1

        assert isp_completeness_event2[0].get_structured_values() == [
            {
                "name": "status",
                "value": "INCOMPLETE",
                "type": "text"
            },
            {
                "name": "downlink_orbit",
                "value": "16078.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2A",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "MPS_",
                "type": "text"
            },
            {
                "name": "playback_type",
                "value": "NOMINAL",
                "type": "text"
            },
            {
                "name": "sensing_orbit",
                "value": "-1.0",
                "type": "double"
            },
            {
                "name": "sad_status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        # Check PLAYBACK_VALIDITY events
        playback_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_%")).all()

        assert len(playback_validity_events) == 3

        # Check specific PLAYBACK_VALIDITY
        playback_validity_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_4",
                                                                                 Event.start == "2018-07-21T10:35:33.728601",
                                                                                 Event.stop == "2018-07-21T10:37:14.719834").all()

        assert len(playback_validity_event1) == 1

        playback_validity_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_20",
                                                                                 Event.start == "2018-07-21T10:35:33.760977",
                                                                                 Event.stop == "2018-07-21T10:37:14.753003").all()

        assert len(playback_validity_event2) == 1

        playback_validity_event3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_2",
                                                                                 Event.start == "2018-07-21T10:37:20.858708",
                                                                                 Event.stop == "2018-07-21T10:37:26.355940").all()

        assert len(playback_validity_event3) == 1

        # Check PLANNED_PLAYBACK_COMPLETENESS_CHANNEL events
        playback_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK_COMPLETENESS_CHANNEL%")).all()

        assert len(playback_completeness_events) == 3

        # Check specific PLANNED_PLAYBACK_COMPLETENESS_CHANNEL
        playback_completeness_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T10:35:33.728601",
                                                                                 Event.stop == "2018-07-21T10:37:14.719834").all()

        assert len(playback_completeness_event1) == 1

        playback_completeness_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T10:35:33.760977",
                                                                                 Event.stop == "2018-07-21T10:37:14.753003").all()

        assert len(playback_completeness_event2) == 1

        playback_completeness_event3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T10:37:20.858708",
                                                                                 Event.stop == "2018-07-21T10:37:26.355940").all()

        assert len(playback_completeness_event3) == 1

        # Check ISP_GAPs events
        isp_gap_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_GAP")).all()

        assert len(isp_gap_events) == 5

        # Check specific ISP_GAP
        isp_gap_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(isp_gap_event1) == 1

        assert isp_gap_event1[0].get_structured_values() == [
            {
                "type": "text",
                "name": "impact",
                "value": "COMPLETE_SCENES_BAND"
            },
            {
                "type": "text",
                "name": "band",
                "value": "2"
            },
            {
                "type": "double",
                "name": "detector",
                "value": "12.0"
            },
            {
                "type": "double",
                "name": "downlink_orbit",
                "value": "16078.0"
            },
            {
                "type": "text",
                "name": "satellite",
                "value": "S2A"
            },
            {
                "type": "text",
                "name": "reception_station",
                "value": "MPS_"
            },
            {
                "type": "double",
                "name": "vcid",
                "value": "4.0"
            },
            {
                "type": "text",
                "name": "playback_type",
                "value": "NOMINAL"
            },
            {
                "type": "double",
                "name": "apid",
                "value": "1.0"
            }
        ]

        isp_gap_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                                 Event.start == "2018-07-21T08:52:29.993268",
                                                                                 Event.stop == "2018-07-21T08:52:31.254806").all()

        assert len(isp_gap_event2) == 1

        assert isp_gap_event2[0].get_structured_values() == [
            {
                "type": "text",
                "name": "impact",
                "value": "AT_BEGINNING"
            },
            {
                "type": "text",
                "name": "band",
                "value": "3"
            },
            {
                "type": "double",
                "name": "detector",
                "value": "12.0"
            },
            {
                "type": "double",
                "name": "downlink_orbit",
                "value": "16078.0"
            },
            {
                "type": "text",
                "name": "satellite",
                "value": "S2A"
            },
            {
                "type": "text",
                "name": "reception_station",
                "value": "MPS_"
            },
            {
                "type": "double",
                "name": "vcid",
                "value": "4.0"
            },
            {
                "type": "text",
                "name": "playback_type",
                "value": "NOMINAL"
            },
            {
                "type": "double",
                "name": "apid",
                "value": "2.0"
            },
            {
                "type": "double",
                "name": "missing_packets",
                "value": "50.0"
            }
        ]

        isp_gap_event3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                                 Event.start == "2018-07-21T08:52:33.601040",
                                                                                 Event.stop == "2018-07-21T08:52:37.209040").all()

        assert len(isp_gap_event3) == 1

        assert isp_gap_event3[0].get_structured_values() == [
            {
                "type": "text",
                "value": "SMALLER_THAN_A_SCENE",
                "name": "impact"
            },
            {
                "type": "text",
                "value": "1",
                "name": "band"
            },
            {
                "type": "double",
                "value": "12.0",
                "name": "detector"
            },
            {
                "type": "double",
                "value": "16078.0",
                "name": "downlink_orbit"
            },
            {
                "type": "text",
                "value": "S2A",
                "name": "satellite"
            },
            {
                "type": "text",
                "value": "MPS_",
                "name": "reception_station"
            },
            {
                "type": "double",
                "value": "4.0",
                "name": "vcid"
            },
            {
                "type": "text",
                "value": "NOMINAL",
                "name": "playback_type"
            },
            {
                "type": "double",
                "value": "0.0",
                "name": "apid"
            },
            {
                "type": "double",
                "value": "23.0",
                "name": "counter_start"
            },
            {
                "type": "double",
                "value": "23.0",
                "name": "counter_stop"
            },
            {
                "type": "double",
                "value": "23.0",
                "name": "missing_packets"
            }
        ]

        isp_gap_event4 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                                 Event.start == "2018-07-21T08:52:37.208811",
                                                                                 Event.stop == "2018-07-21T08:52:38.777507").all()

        assert len(isp_gap_event4) == 1

        assert isp_gap_event4[0].get_structured_values() == [
            {
                "name": "impact",
                "type": "text",
                "value": "SMALLER_THAN_A_SCENE"
            },
            {
                "name": "band",
                "type": "text",
                "value": "1"
            },
            {
                "name": "detector",
                "type": "double",
                "value": "12.0"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "MPS_"
            },
            {
                "name": "vcid",
                "type": "double",
                "value": "4.0"
            },
            {
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },
            {
                "name": "apid",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "counter_start",
                "type": "double",
                "value": "23.0"
            },
            {
                "name": "counter_stop",
                "type": "double",
                "value": "10.0"
            },
            {
                "name": "missing_packets",
                "type": "double",
                "value": "10.0"
            }
        ]

        isp_gap_event5 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                                 Event.start == "2018-07-21T08:52:38.777279",
                                                                                 Event.stop == "2018-07-21T08:52:40.032235").all()

        assert len(isp_gap_event5) == 1

        assert isp_gap_event5[0].get_structured_values() == [
            {
                "name": "impact",
                "type": "text",
                "value": "SMALLER_THAN_A_SCENE"
            },
            {
                "name": "band",
                "type": "text",
                "value": "1"
            },
            {
                "name": "detector",
                "type": "double",
                "value": "12.0"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "MPS_"
            },
            {
                "name": "vcid",
                "type": "double",
                "value": "4.0"
            },
            {
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },
            {
                "name": "apid",
                "type": "double",
                "value": "0.0"
            },
            {
                "name": "counter_start",
                "type": "double",
                "value": "10.0"
            },
            {
                "name": "counter_stop",
                "type": "double",
                "value": "18.0"
            },
            {
                "name": "missing_packets",
                "type": "double",
                "value": "8.0"
            }
        ]

    def test_insert_rep_pass_with_two_datablocks(self):
        filename = "S2A_REP_PASS_CONTAINING_TWO_DATABLOCKS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 17

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T23:18:43",
                                                    Source.reported_validity_stop == "2018-07-21T23:30:15",
                                                    Source.validity_start == "2018-07-21T08:54:26.359237",
                                                   Source.validity_stop == "2018-07-21T23:30:15").all()

        assert len(sources) == 2

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "16086.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
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

        assert len(isp_validities) == 2

        # Check specific ISP_VALIDITY
        specific_isp_validity1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2018-07-21T18:51:28.225563",
                                                                                 Event.stop == "2018-07-21T18:55:29.946495").all()

        assert len(specific_isp_validity1) == 1

        specific_isp_validity2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2018-07-21T20:18:50.458085",
                                                                                 Event.stop == "2018-07-21T20:26:39.468624").all()

        assert len(specific_isp_validity2) == 1

        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(isp_completeness_events) == 4

        # Check specific ISP_VALIDITY
        isp_completeness_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T18:51:28.225563",
                                                                                 Event.stop == "2018-07-21T18:55:29.946495").all()

        assert len(isp_completeness_event1) == 1

        # Check specific ISP_VALIDITY
        isp_completeness_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T18:51:28.225563",
                                                                                 Event.stop == "2018-07-21T18:55:29.946495").all()

        assert len(isp_completeness_event2) == 1

        isp_completeness_event3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T20:18:50.458085",
                                                                                 Event.stop == "2018-07-21T20:26:39.468624").all()

        assert len(isp_completeness_event3) == 1

        isp_completeness_event4 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2",
                                                                                 Event.start == "2018-07-21T20:18:50.458085",
                                                                                 Event.stop == "2018-07-21T20:26:39.468624").all()

        assert len(isp_completeness_event4) == 1

    def test_insert_rep_pass_no_data(self):
        filename = "S2A_REP_PASS_NO_DATA.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 1

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T10:35:27",
                                                   Source.validity_stop == "2018-07-21T10:37:39").all()

        assert len(sources) == 2

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "16078.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
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

    def test_insert_rep_pass_with_playback_gaps(self):
        filename = "S2A_REP_PASS_CONTAINING_PLAYBACK_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 15

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39").all()

        assert len(sources) == 2

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "16078.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2A",
                "type": "text",
                "name": "satellite"
            },
            {
                "value": "MPS_",
                "type": "text",
                "name": "reception_station"
            },
            {
                "value": "COMPLETE",
                "type": "text",
                "name": "isp_status"
            },
            {
                "value": "INCOMPLETE",
                "type": "text",
                "name": "acquisition_status"
            }
        ]

        # Check specific PLAYBACK_GAP
        playback_gap = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_GAP",
                                                                                 Event.start == "2018-07-21T10:36:12.525910",
                                                                                 Event.stop == "2018-07-21T10:36:12.585768").all()

        assert len(playback_gap) == 1

        assert playback_gap[0].get_structured_values() == [
            {
                "type": "double",
                "name": "downlink_orbit",
                "value": "16078.0"
            },
            {
                "type": "text",
                "name": "satellite",
                "value": "S2A"
            },
            {
                "type": "text",
                "name": "reception_station",
                "value": "MPS_"
            },
            {
                "type": "double",
                "name": "channel",
                "value": "1.0"
            },
            {
                "type": "double",
                "name": "vcid",
                "value": "4.0"
            },
            {
                "type": "text",
                "name": "playback_type",
                "value": "NOMINAL"
            }
        ]

    def test_insert_rep_pass_with_plan(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check sources
        sources = self.session.query(Source).all()

        assert len(sources) == 8
        
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39",
                                                   Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF",
                                                   Source.processor == "ingestion_dfep_acquisition.py").all()

        assert len(sources) == 2

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T08:52:29.993268",
                                                   Source.validity_stop == "2018-07-21T08:54:18.226646",
                                                   Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF",
                                                   Source.processor == "isp_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T10:35:33.728601",
                                                   Source.validity_stop == "2018-07-21T10:37:26.355940",
                                                   Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF",
                                                   Source.processor == "playback_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF").all()

        assert len(events) == 22

        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(isp_completeness_events) == 6

        # Check specific ISP completeness
        isp_completeness_missing_left = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_%"),
                                                                                 Event.start == "2018-07-21T08:36:08.255634",
                                                                                 Event.stop == "2018-07-21T08:52:29.993268").all()

        assert len(isp_completeness_missing_left) == 2

        isp_completeness_statuses = [event for event in isp_completeness_missing_left if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(isp_completeness_statuses) == 2

        isp_completeness_missing_right = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_%"),
                                                                                 Event.start == "2018-07-21T08:54:18.226646",
                                                                                 Event.stop == "2018-07-21T09:08:50.195941").all()

        assert len(isp_completeness_missing_left) == 2

        isp_completeness_statuses = [event for event in isp_completeness_missing_right if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(isp_completeness_statuses) == 2

        # Check number of annotations generated
        annotations = self.session.query(Annotation).join(Source).filter(Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF").all()

        assert len(annotations) == 1

    def test_insert_rep_pass_only_hktm_with_plan(self):

        filename = "S2A_NPPF_ONLY_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE_ONLY_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_ONLY_HKTM.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check sources
        sources = self.session.query(Source).all()

        assert len(sources) == 7
        
        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T01:47:36",
                                                    Source.reported_validity_stop == "2018-07-21T01:47:51",
                                                    Source.validity_start == "2018-07-21 01:47:36",
                                                   Source.validity_stop == "2018-07-21T01:47:51",
                                                   Source.name == "S2A_REP_PASS_ONLY_HKTM.EOF",
                                                   Source.processor == "ingestion_dfep_acquisition.py").all()

        assert len(source) == 2

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T01:47:36",
                                                    Source.reported_validity_stop == "2018-07-21T01:47:51",
                                                    Source.validity_start == "2018-07-21T01:47:42.854151",
                                                   Source.validity_stop == "2018-07-21T01:47:43.833085",
                                                   Source.name == "S2A_REP_PASS_ONLY_HKTM.EOF",
                                                   Source.processor == "playback_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == "S2A_REP_PASS_ONLY_HKTM.EOF").all()

        assert len(events) == 4

        # Check number of annotations generated
        annotations = self.session.query(Annotation).join(Source).filter(Source.name == "S2A_REP_PASS_ONLY_HKTM.EOF").all()

        assert len(annotations) == 1

        # Check DISTRIBUTION_STATUS events
        distribution_status_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_%_DISTRIBUTION_STATUS%")).all()

        assert len(distribution_status_events) == 1

        # Check specific DISTRIBUTION_STATUS event
        distribution_status_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_HKTM_DISTRIBUTION_STATUS_CHANNEL_1",
                                                                                 Event.start == "2018-07-21T01:47:42.854151",
                                                                                 Event.stop == "2018-07-21T01:47:43.833085").all()

        assert len(distribution_status_event1) == 1

        assert distribution_status_event1[0].get_structured_values() == [
            {
                "name": "status",
                "type": "text",
                "value": "DELIVERED"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "16073.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },
            {
                "name": "channel",
                "type": "double",
                "value": "1.0"
            },
            {
                "name": "completeness_status",
                "type": "text",
                "value": "OK"
            },
            {
                "name": "number_of_received_transfer_frames",
                "type": "double",
                "value": "16764.0"
            },
            {
                "name": "number_of_distributed_transfer_frames",
                "type": "double",
                "value": "16764.0"
            },
            {
                "name": "completeness_difference",
                "type": "double",
                "value": "0.0"
            },
            {"name": "footprint_details",
             "type": "object",
             "values": [{"name": "footprint",
                         "type": "geometry",
                         "value": "POLYGON ((-78.683432 70.397443, -71.60281000000001 71.63375499999999, -71.60281000000001 71.63375499999999, -78.683432 70.397443))"}]}
        ]

    def test_insert_rep_pass_playback_rt_with_plan(self):

        filename = "S2A_NPPF_PLAYBACK_RT.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_PLAYBACK_RT.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check sources
        sources = self.session.query(Source).all()

        assert len(sources) == 8

        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39",
                                                   Source.name == "S2A_REP_PASS_PLAYBACK_RT.EOF",
                                                   Source.processor == "ingestion_dfep_acquisition.py").all()

        assert len(sources) == 2

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T08:52:29.993268",
                                                   Source.validity_stop == "2018-07-21T08:54:18.226646",
                                                   Source.name == "S2A_REP_PASS_PLAYBACK_RT.EOF",
                                                   Source.processor == "isp_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T10:35:33.728601",
                                                   Source.validity_stop == "2018-07-21T10:37:26.355940",
                                                   Source.name == "S2A_REP_PASS_PLAYBACK_RT.EOF",
                                                   Source.processor == "playback_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == "S2A_REP_PASS_PLAYBACK_RT.EOF").all()

        assert len(events) == 22

        # Check number of annotations generated
        annotations = self.session.query(Annotation).join(Source).filter(Source.name == "S2A_REP_PASS_PLAYBACK_RT.EOF").all()

        assert len(annotations) == 1

    def test_insert_rep_pass_with_planned_small_playback(self):

        filename = "S2A_NPPF_SMALL_PLAYBACK.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check sources
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39",
                                                   Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF",
                                                   Source.processor == "ingestion_dfep_acquisition.py").all()

        assert len(sources) == 2

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T08:52:29.993268",
                                                   Source.validity_stop == "2018-07-21T08:54:18.226646",
                                                   Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF",
                                                   Source.processor == "isp_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1

        source = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-21T10:35:33.728601",
                                                   Source.validity_stop == "2018-07-21T10:37:26.355940",
                                                   Source.name == "S2A_REP_PASS_CONTAINING_ALL_DATA_TO_BE_PROCESS.EOF",
                                                   Source.processor == "playback_planning_completeness_ingestion_dfep_acquisition.py").all()

        assert len(source) == 1


    def test_insert_rep_pass_with_gaps_at_the_end(self):

        filename = "S2A_REP_PASS_GAPS_AT_THE_END_APID.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check sources
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T10:35:27",
                                                    Source.reported_validity_stop == "2018-07-21T10:37:39",
                                                    Source.validity_start == "2018-07-20T22:00:12.859222",
                                                   Source.validity_stop == "2018-07-21T10:37:39",
                                                   Source.name == filename,
                                                   Source.processor == "ingestion_dfep_acquisition.py").all()

        assert len(sources) == 2

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == filename).all()

        assert len(events) == 15

        isp_gap_event = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                     Event.start == "2018-07-21T08:53:56.579788",
                                                                     Event.stop == "2018-07-21T08:54:18.226646").all()

        assert len(isp_gap_event) == 1

    def test_insert_rep_pass_with_two_datablocks_with_gaps(self):

        filename = "S2A_REP_PASS_CONTAINING_TWO_DATABLOCKS_WITH_GAPS.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check sources
        sources = self.session.query(Source).filter(Source.reported_validity_start == "2018-07-21T23:18:43",
                                                    Source.reported_validity_stop == "2018-07-21T23:30:15",
                                                    Source.validity_start == "2018-07-21T08:54:26.359237",
                                                   Source.validity_stop == "2018-07-21T23:30:15",
                                                   Source.name == filename,
                                                   Source.processor == "ingestion_dfep_acquisition.py").all()

        assert len(sources) == 2

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == filename).all()

        assert len(events) == 18

        isp_gap_event = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                     Event.start == "2018-07-21T20:18:50.458085",
                                                                     Event.stop == "2018-07-21T20:19:15.712714").all()

        assert len(isp_gap_event) == 1

    def test_insert_rep_pass_with_only_half_swath(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_REP_PASS_CONTAINING_ONLY_HALF_SWATH.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_acquisition.ingestion_dfep_acquisition", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        isp_gap_events = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP").all()

        assert len(isp_gap_events) == 78
