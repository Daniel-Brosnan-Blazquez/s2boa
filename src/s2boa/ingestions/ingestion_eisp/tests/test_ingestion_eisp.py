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

        assert len(events) == 18

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check DFEP_ACQUISITION_VALIDITY event
        dfep_acquisition_validity = self.session.query(Event).join(Gauge).filter(Gauge.name == "DFEP_ACQUISITION_VALIDITY",
                                                                                 Event.start == "2021-02-26T18:01:18",
                                                                                 Event.stop == "2021-02-26T18:09:28").all()

        assert len(dfep_acquisition_validity) == 1

        assert dfep_acquisition_validity[0].get_structured_values() == [
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
            }
        ]

        assert len(dfep_acquisition_validity[0].eventLinks) == 0

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

        assert len(events) == 59

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

        assert len(events) == 26

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

        # Check DFEP_ACQUISITION_VALIDITY event
        dfep_acquisition_validity = self.session.query(Event).join(Gauge).filter(Gauge.name == "DFEP_ACQUISITION_VALIDITY",
                                                                                 Event.start == "2021-02-26T18:01:18",
                                                                                 Event.stop == "2021-02-26T18:09:28").all()

        assert len(dfep_acquisition_validity) == 1

        assert dfep_acquisition_validity[0].get_structured_values() == [
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
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((49.395836 60.004485, 49.234451 60.207975, 49.071228 60.411291, 48.906135 60.614429, 48.739088 60.817381, 48.570048 61.020143, 48.399054 61.222721, 48.225995 61.425102, 48.05082 61.627281, 47.873514 61.829258, 47.694065 62.031033, 47.512366 62.232593, 47.328371 62.433934, 47.142101 62.635061, 46.953461 62.835962, 46.762376 63.03663, 46.568811 63.237061, 46.372776 63.43726, 46.174137 63.63721, 45.972837 63.836906, 45.768878 64.036349, 45.56218 64.235533, 45.352644 64.434445, 45.140209 64.633079, 44.924907 64.83144299999999, 44.706574 65.029517, 44.485141 65.22729200000001, 44.260585 65.42477, 44.032845 65.621945, 43.80179 65.81880099999999, 43.567344 66.01533000000001, 43.329523 66.211539, 43.088167 66.407408, 42.843179 66.602925, 42.594507 66.79808800000001, 42.342108 66.99289400000001, 42.085816 67.18732300000001, 41.825538 67.381365, 41.561261 67.575023, 41.292837 67.76827900000001, 41.020134 67.961117, 40.743065 68.15353, 40.461607 68.34551999999999, 40.17555 68.53706, 39.884782 68.72813600000001, 39.589254 68.91874900000001, 39.288832 69.10888199999999, 38.98334 69.29851499999999, 38.672651 69.487633, 38.35676 69.676243, 38.035409 69.86431, 37.708461 70.05181899999999, 37.375826 70.238764, 37.03738 70.42513099999999, 36.692899 70.61089200000001, 36.342227 70.79602800000001, 35.985318 70.980543, 35.621918 71.1644, 35.251838 71.347578, 34.874942 71.530063, 34.491114 71.711845, 34.100075 71.892886, 33.701636 72.07316400000001, 33.295701 72.252672, 32.882018 72.431378, 32.460344 72.60924900000001, 32.030485 72.78626199999999, 31.592336 72.962412, 31.145553 73.137647, 30.689912 73.31194000000001, 30.225261 73.485275, 29.751351 73.65761999999999, 29.267877 73.82893, 28.774591 73.999172, 28.271384 74.168341, 27.75786 74.33637400000001, 27.233753 74.50323299999999, 26.698854 74.668892, 26.152921 74.833319, 25.595589 74.996455, 25.026575 75.15825599999999, 24.445717 75.31870600000001, 23.85263 75.477738, 23.246995 75.635301, 22.628554 75.791354, 21.997086 75.945863, 21.35218 76.098752, 20.693535 76.249966, 20.020953 76.399475, 19.334085 76.547208, 18.632584 76.693095, 17.91617 76.83707800000001, 17.184678 76.979125, 16.437685 77.11913699999999, 15.674917 77.257048, 14.896183 77.392808, 14.10122 77.526347, 13.28971 77.657573, 12.461424 77.786411, 11.616285 77.912825, 10.753966 78.0367, 9.874286 78.157956, 8.977145999999999 78.27652500000001, 8.062455999999999 78.392338, 7.130032 78.505284, 6.179811 78.615278, 5.211868 78.722268, 4.22613 78.826143, 3.222619 78.926805, 2.201455 79.024176, 1.162841 79.11819300000001, 0.106866 79.208733, -0.966231 79.295709, -2.056087 79.37906099999999, -3.162393 79.458692, -4.284781 79.53449999999999, -5.422779 79.606403, -6.575785 79.674362, -7.743305 79.738255, -8.92469 79.79800299999999, -10.119194 79.853559, -11.326056 79.904854, -12.544488 79.951798, -13.773606 79.99432899999999, -15.012426 80.032437, -16.260014 80.06603, -17.515342 80.095056, -18.777323 80.11949300000001, -20.044844 80.139324, -21.316786 80.154487, -22.591983 80.164959, -23.869245 80.170767, -25.14712 80.168909, -26.425211 80.16826399999999, -27.701517 80.15995599999999, -28.97513 80.146991, -30.429369 82.752683, -28.714258 82.770171, -26.992452 82.781389, -25.266194 82.782263, -23.540473 82.784773, -21.816282 82.776933, -20.097232 82.76280199999999, -18.386256 82.74236500000001, -16.686196 82.715673, -14.999722 82.68284199999999, -13.329432 82.64393099999999, -11.677791 82.599013, -10.047053 82.548202, -8.439159999999999 82.491674, -6.856106 82.429496, -5.299562 82.361805, -3.770898 82.28878, -2.271357 82.21057, -0.802084 82.127298, 0.636062 82.03912099999999, 2.04262 81.94626100000001, 3.416917 81.848823, 4.758606 81.746965, 6.0676 81.64087000000001, 7.343943 81.530714, 8.587569 81.416616, 9.798679999999999 81.29873000000001, 10.977791 81.17725299999999, 12.12515 81.0523, 13.241167 80.92400000000001, 14.326433 80.792507, 15.3817 80.657985, 16.407384 80.520522, 17.404153 80.38024299999999, 18.372882 80.237302, 19.314219 80.09180000000001, 20.228792 79.943832, 21.117359 79.793505, 21.980921 79.64096600000001, 22.819957 79.486265, 23.63521 79.329498, 24.427554 79.17077399999999, 25.197726 79.010181, 25.946296 78.847776, 26.673967 78.683637, 27.381678 78.517876, 28.069874 78.35052899999999, 28.739186 78.181659, 29.390338 78.011343, 30.024043 77.83965600000001, 30.640717 77.666628, 31.240943 77.492315, 31.825485 77.31679800000001, 32.394749 77.140107, 32.949199 76.96228000000001, 33.489388 76.78337000000001, 34.015971 76.603444, 34.529209 76.422511, 35.029557 76.240611, 35.517607 76.057804, 35.993728 75.874116, 36.458226 75.68956799999999, 36.911503 75.504194, 37.354164 75.318056, 37.786333 75.131151, 38.208362 74.943506, 38.620693 74.75516399999999, 39.02367 74.566153, 39.417474 74.376479, 39.802406 74.186167, 40.178952 73.995265, 40.547216 73.803771, 40.907437 73.61170300000001, 41.259938 73.419089, 41.605049 73.22595800000001, 41.942856 73.032309, 42.273587 72.838159, 42.597614 72.64354400000001, 42.915053 72.44846800000001, 43.226048 72.252937, 43.530828 72.056971, 43.829722 71.860601, 44.122738 71.66381800000001, 44.410051 71.46663700000001, 44.691944 71.269082, 44.968549 71.071161, 45.239937 70.872877, 45.50626 70.674239, 45.767856 70.47528200000001, 46.02467 70.275991, 46.276841 70.07637800000001, 46.524576 69.87645999999999, 46.76803 69.676249, 47.007216 69.475742, 47.242252 69.274947, 47.473406 69.07388899999999, 47.700658 68.872562, 47.924088 68.67097, 48.143847 68.469126, 48.360111 68.267044, 48.572849 68.064718, 48.782153 67.862154, 48.988231 67.659372, 49.1911 67.456369, 49.390794 67.253146, 49.587414 67.04971, 49.781161 66.846081, 49.971965 66.642247, 50.159902 66.438215, 50.345129 66.233997, 50.527698 66.02959799999999, 50.707604 65.825013, 50.884913 65.620248, 51.059836 65.415322, 51.232287 65.210224, 51.402322 65.004958, 51.570057 64.799533, 51.735576 64.593957, 51.898844 64.388223, 52.059913 64.18233600000001, 52.218952 63.97631, 52.375916 63.77014, 52.530828 63.563826, 52.683767 63.357374, 52.834851 63.150796, 52.984015 62.944082, 53.131304 62.737235, 53.276849 62.530269, 53.420643 62.32318, 53.56268 62.115967, 53.703011 61.908633, 53.84178 61.701192, 53.978901 61.493634, 54.11441 61.285961, 54.248409 61.078182, 54.380923 60.870299, 49.395836 60.004485))"
                    }
                ]
            }
        ]

        assert len(dfep_acquisition_validity[0].eventLinks) == 2
        
        # Check playbacks
        # Check playback for MSI
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

        # Check links of DFEP_ACQUISITION_VALIDITY with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(dfep_acquisition_validity[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "DFEP_ACQUISITION_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(dfep_acquisition_validity[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_from_plan) == 1

        # Check playback for HKTM
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

        # Check links of DFEP_ACQUISITION_VALIDITY with plan
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(dfep_acquisition_validity[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "DFEP_ACQUISITION_VALIDITY", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback[0].event_uuid)], "op": "in"},
                                                       event_uuids = {"filter": [str(dfep_acquisition_validity[0].event_uuid)], "op": "in"},
                                                       link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_from_plan) == 1
