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

        isp_validities.sort(key=lambda x: x.start)

        # Check specific ISP_VALIDITY
        specific_isp_validity1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T15:08:54.264729",
                                                                                 Event.stop == "2021-02-26T15:17:44.607184").all()

        assert len(specific_isp_validity1) == 1

        # Check specific ISP_VALIDITY
        specific_isp_validity2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T15:22:13.855720",
                                                                                 Event.stop == "2021-02-26T15:22:53.541439").all()

        assert len(specific_isp_validity2) == 1

        # Check specific ISP_VALIDITY
        specific_isp_validity3 = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY",
                                                                                 Event.start == "2021-02-26T16:32:24.848297",
                                                                                 Event.stop == "2021-02-26T16:35:32.452882").all()

        assert len(specific_isp_validity3) == 1

        assert specific_isp_validity3[0].get_structured_values() == [
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

        for isp_validity in isp_validities:
            # Check links with RAW_ISP_VALIDITY
            link_to_raw_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                           event_uuids = {"filter": [str(specific_raw_isp_validity[0].event_uuid)], "op": "in"},
                                                           link_names = {"filter": "ISP_VALIDITY", "op": "like"})

            assert len(link_to_raw_isp_validity) == 1

            link_from_raw_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(specific_raw_isp_validity[0].event_uuid)], "op": "in"},
                                                           event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                           link_names = {"filter": "RAW_ISP_VALIDITY", "op": "like"})
            
            assert len(link_from_raw_isp_validity) == 1
        # end for
        
        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        planned_isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(planned_isp_completeness_events) == 3

        # Check specific PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL
        specific_planned_isp_completeness = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2021-02-26T15:08:54.264729",
                                                                                 Event.stop == "2021-02-26T15:17:44.607184").all()

        assert len(specific_planned_isp_completeness) == 1

        # Check links with ISP_VALIDITY
        link_to_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(specific_planned_isp_completeness[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(specific_raw_isp_validity[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "ISP_VALIDITY", "op": "like"})

        assert len(link_to_raw_isp_validity) == 1

        link_from_raw_isp_validity = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(specific_raw_isp_validity[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                       link_names = {"filter": "RAW_ISP_VALIDITY", "op": "like"})

        assert len(link_from_raw_isp_validity) == 1


        # Check specific PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL
        specific_planned_isp_completeness = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2021-02-26T15:22:13.855720",
                                                                                 Event.stop == "2021-02-26T15:22:53.541439").all()

        assert len(specific_planned_isp_completeness) == 1

        # Check specific PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL
        specific_planned_isp_completeness = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                                                                                 Event.start == "2021-02-26T16:32:24.848297",
                                                                                 Event.stop == "2021-02-26T16:35:32.452882").all()

        assert len(specific_planned_isp_completeness) == 1

        assert specific_planned_isp_completeness[0].get_structured_values() == [
            {
                "value": "RECEIVED",
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

        # Check ISP_VALIDITY_PROCESSING_COMPLETENESS_CHANNEL events
        processing_isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_VALIDITY_PROCESSING_COMPLETENESS%")).all()

        assert len(processing_isp_completeness_events) == 6

        # Check specific ISP_VALIDITY_PROCESSING_COMPLETENESS_CHANNEL
        specific_processing_isp_completeness = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_VALIDITY_PROCESSING_COMPLETENESS%"),
                                                                                 Event.start == "2021-02-26T15:09:00.264729",
                                                                                 Event.stop == "2021-02-26T15:17:38.607184").all()

        assert len(specific_processing_isp_completeness) == 2

        # Check specific ISP_VALIDITY_PROCESSING_COMPLETENESS_CHANNEL
        specific_processing_isp_completeness = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_VALIDITY_PROCESSING_COMPLETENESS%"),
                                                                                 Event.start == "2021-02-26T15:22:19.855720",
                                                                                 Event.stop == "2021-02-26T15:22:47.541439").all()

        assert len(specific_processing_isp_completeness) == 2

        # Check specific ISP_VALIDITY_PROCESSING_COMPLETENESS_CHANNEL
        specific_processing_isp_completeness = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_VALIDITY_PROCESSING_COMPLETENESS%"),
                                                                                 Event.start == "2021-02-26T16:32:30.848297",
                                                                                 Event.stop == "2021-02-26T16:35:26.452882").all()

        assert len(specific_processing_isp_completeness) == 2

        # Check specific ISP_VALIDITY_PROCESSING_COMPLETENESS_CHANNEL
        specific_processing_isp_completeness_l0 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_VALIDITY_PROCESSING_COMPLETENESS_L0%"),
                                                                                 Event.start == "2021-02-26T16:32:30.848297",
                                                                                 Event.stop == "2021-02-26T16:35:26.452882").all()

        assert len(specific_processing_isp_completeness_l0) == 1

        assert specific_processing_isp_completeness_l0[0].get_structured_values() == [
            {
                "value": "MISSING",
                "name": "status",
                "type": "text"
            },
            {
                "value": "L0",
                "name": "level",
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

    def test_insert_rep_pass_with_gaps(self):

        filename = "S2A_OPER_REP_PASS_E_VGS1_20210226T182947_V20210226T181325_20210226T181753.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 58

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check LINK_DETAILS events
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS_CH2").all()

        assert len(link_details) == 1

        # Check ISP_VALIDITY events
        isp_validities = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY").all()

        assert len(isp_validities) == 1

        # Check ISP_GAP events
        isp_gaps = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP").all()

        assert len(isp_gaps) == 48

        # Check ISP_GAP events
        isp_gaps = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                Event.start == "2021-02-26T16:36:08.530370",
                                                                Event.stop == "2021-02-26T16:36:12.137914").all()

        assert len(isp_gaps) == 30

        # Check ISP_GAP events
        isp_gaps = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                Event.start == "2021-02-26T16:36:08.530370",
                                                                Event.stop == "2021-02-26T16:36:08.555601").all()

        assert len(isp_gaps) == 1

        assert isp_gaps[0].get_structured_values() == [
            {
                "value": "SMALLER_THAN_A_SCENE",
                "name": "impact",
                "type": "text"
            },
            {
                "value": "8",
                "name": "band",
                "type": "text"
            },
            {
                "value": "1.0",
                "name": "detector",
                "type": "double"
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
                "value": "INS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "20.0",
                "name": "vcid",
                "type": "double"
            },
            {
                "value": "NOMINAL",
                "name": "playback_type",
                "type": "text"
            },
            {
                "value": "343.0",
                "name": "apid",
                "type": "double"
            },
            {
                "value": "143.0",
                "name": "counter_start",
                "type": "double"
            },
            {
                "value": "1.0",
                "name": "counter_stop",
                "type": "double"
            },
            {
                "value": "1.0",
                "name": "missing_packets",
                "type": "double"
            }
        ]

        # Check PLAYBACK_GAP events
        playback_gaps = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_GAP",
                                                                Event.start == "2021-02-26T18:13:57.790842",
                                                                Event.stop == "2021-02-26T18:13:57.903010").all()

        assert len(playback_gaps) == 1

        assert playback_gaps[0].get_structured_values() == [
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
                "value": "INS_",
                "name": "reception_station",
                "type": "text"
            },
            {
                "value": "2.0",
                "name": "channel",
                "type": "double"
            },
            {
                "value": "20.0",
                "name": "vcid",
                "type": "double"
            },{
                "value": "NOMINAL",
                "name": "playback_type",
                "type": "text"
            }
        ]

    def test_insert_rep_pass_no_data(self):
        filename = "S2A_REP_PASS_NO_DATA.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 0

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 0

        # Check number of sources generated
        sources = self.session.query(Source).all()

        assert len(sources) == 1
        
    def test_insert_several_rep_pass_with_plan(self):

        filename = "S2A_OPER_MPL__NPPF__20210225T120000_20210315T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_ORBPRE_20210226T030234_20210308T030234_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_SPSGS__PDMC_20210225T090001_V20210226T090000_20210304T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2A_OPER_MPL_SPINS__PDMC_20210225T090002_V20210226T090000_20210304T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2__OPER_SRA_EDRS_A_PDMC_20210226T030000_V20210226T030000_20210430T235620.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_slot_request_edrs.ingestion_slot_request_edrs", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2A_OPER_REP_PASS_E_EDRS_20210226T103748_V20210226T101706_20210226T102330.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_EDRS_20210226T103805_V20210226T101706_20210226T102347.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_VGS1_20210226T100917_V20210226T093725_20210226T094124.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_VGS1_20210226T100931_V20210226T093726_20210226T094138.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_VGS1_20210226T182926_V20210226T181324_20210226T181733.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_VGS1_20210226T182947_V20210226T181325_20210226T181753.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_VGS2_20210226T182315_V20210226T180119_20210226T180908.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_REP_PASS_E_VGS2_20210226T182335_V20210226T180118_20210226T180928.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

    def test_insert_rep_pass_with_plan(self):

        filename = "S2A_OPER_MPL__NPPF__20210225T120000_20210315T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_ORBPRE_20210226T030234_20210308T030234_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_SPSGS__PDMC_20210225T090001_V20210226T090000_20210304T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0
        
        filename = "S2A_OPER_REP_PASS_E_VGS2_20210226T182335_V20210226T180118_20210226T180928.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_eisp.ingestion_eisp", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == "S2A_OPER_REP_PASS_E_VGS2_20210226T182335_V20210226T180118_20210226T180928.EOF").all()

        assert len(events) == 25

        # Get relevant planned_cut_imaging
        planned_cut_imaging_1 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_CUT_IMAGING"),
                                                                                 Event.start == "2021-02-26T15:07:13.205000",
                                                                                 Event.stop == "2021-02-26T15:17:40.536000").all()

        assert len(planned_cut_imaging_1) == 1

        planned_cut_imaging_2 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_CUT_IMAGING"),
                                                                                 Event.start == "2021-02-26T15:22:10.636000",
                                                                                 Event.stop == "2021-02-26T15:22:49.216000").all()

        assert len(planned_cut_imaging_2) == 1

        planned_cut_imaging_3 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_CUT_IMAGING"),
                                                                                 Event.start == "2021-02-26T16:32:21.258000",
                                                                                 Event.stop == "2021-02-26T16:49:46.337000").all()

        assert len(planned_cut_imaging_3) == 1

        planned_cut_imagings = [planned_cut_imaging_1[0], planned_cut_imaging_2[0], planned_cut_imaging_3[0]]
        
        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).join(Source).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%"), Source.name == "S2A_OPER_REP_PASS_E_VGS2_20210226T182335_V20210226T180118_20210226T180928.EOF").all()

        assert len(isp_completeness_events) == 3

        # Check specific ISP completeness
        isp_completeness_1 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1"),
                                                                                 Event.start == "2021-02-26T15:08:54.264729",
                                                                                 Event.stop == "2021-02-26T15:17:44.607184").all()

        assert len(isp_completeness_1) == 1

        isp_completeness_statuses = [event for event in isp_completeness_1 if len([value for value in event.eventTexts if value.name == "status" and value.value == "RECEIVED"]) > 0]

        assert len(isp_completeness_statuses) == 1

        # Check links with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(isp_completeness_1[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_cut_imaging_1[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "ISP_COMPLETENESS", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_cut_imaging_1[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(isp_completeness_1[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1

        isp_completeness_2 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1"),
                                                                                 Event.start == "2021-02-26T15:22:13.855720",
                                                                                 Event.stop == "2021-02-26T15:22:53.541439").all()

        assert len(isp_completeness_2) == 1

        isp_completeness_statuses = [event for event in isp_completeness_2 if len([value for value in event.eventTexts if value.name == "status" and value.value == "RECEIVED"]) > 0]

        assert len(isp_completeness_statuses) == 1

        # Check links with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(isp_completeness_2[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_cut_imaging_2[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "ISP_COMPLETENESS", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_cut_imaging_2[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(isp_completeness_2[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1
        
        isp_completeness_3 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1"),
                                                                                 Event.start == "2021-02-26T16:32:24.848297",
                                                                                 Event.stop == "2021-02-26T16:35:32.452882").all()

        assert len(isp_completeness_3) == 1

        isp_completeness_statuses = [event for event in isp_completeness_2 if len([value for value in event.eventTexts if value.name == "status" and value.value == "RECEIVED"]) > 0]

        assert len(isp_completeness_statuses) == 1

        # Check links with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(isp_completeness_3[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_cut_imaging_3[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "ISP_COMPLETENESS", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_cut_imaging_3[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(isp_completeness_3[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

        assert len(link_from_plan) == 1

        # Check ISP_VALIDITY events
        isp_validities = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_VALIDITY").all()

        assert len(isp_validities) == 3

        isp_validities.sort(key=lambda x: x.start)

        i = 0
        for isp_validity in isp_validities:
            # Check links with plan
            link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                           event_uuids = {"filter": [str(planned_cut_imagings[i].event_uuid)], "op": "in"},
                                                           link_names = {"filter": "ISP_VALIDITY", "op": "like"})

            assert len(link_to_plan) == 1

            link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_cut_imagings[i].event_uuid)], "op": "in"},
                                                           event_uuids = {"filter": [str(isp_validity.event_uuid)], "op": "in"},
                                                           link_names = {"filter": "PLANNED_IMAGING", "op": "like"})

            assert len(link_from_plan) == 1
            i += 1
        # end for
        
        # Check playbacks
        playback_validity_4 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_4"),
                                                                                 Event.start == "2021-02-26T18:01:23.007471",
                                                                                 Event.stop == "2021-02-26T18:08:42.798204").all()

        assert len(playback_validity_4) == 1

        planned_playback = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK"),
                                                                                 Event.start == "2021-02-26T18:01:12.603000",
                                                                                 Event.stop == "2021-02-26T18:12:52.038000").all()

        assert len(planned_playback) == 1
        
        # Check links with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(playback_validity_4[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLAYBACK_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(playback_validity_4[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_from_plan) == 1

        playback_validity_3 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_3"),
                                                                                 Event.start == "2021-02-26T18:08:43.072530",
                                                                                 Event.stop == "2021-02-26T18:09:23.609233").all()

        assert len(playback_validity_3) == 1

        planned_playback = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK"),
                                                                                 Event.start == "2021-02-26T18:13:03.038000",
                                                                                 Event.stop == "2021-02-26T18:13:03.038000").all()

        assert len(planned_playback) == 1
        
        # Check links with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(playback_validity_3[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLAYBACK_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(playback_validity_3[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_from_plan) == 1
