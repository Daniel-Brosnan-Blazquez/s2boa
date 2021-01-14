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

class TestVgsAcquisitionIngestion(unittest.TestCase):
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

    def test_insert_rep_pass_with_sad(self):
        filename = "S2A_OPER_REP_PASS_E_VGS2_20200616T105604_V20200616T104814_20200616T105603.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check number of sources generated
        sources = self.session.query(Source).all()

        assert len(sources) == 2

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        source = self.session.query(Source).filter(Source.reported_validity_start == "2020-06-16T10:48:14",
                                                   Source.reported_validity_stop == "2020-06-16T10:56:03",
                                                   Source.validity_start == "2020-06-15T21:02:44.999376",
                                                   Source.validity_stop == "2020-06-16T10:56:03.533806").all()

        assert len(source) == 2

        dim_signatures = self.session.query(DimSignature).all()

        # Check number of dim_signatures generated
        assert len(dim_signatures) == 2

        dim_signature = self.session.query(DimSignature).filter(DimSignature.dim_signature == "RECEPTION_S2A").all()

        assert len(dim_signature) == 1

        dim_signature = self.session.query(DimSignature).filter(DimSignature.dim_signature == "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A").all()

        assert len(dim_signature) == 1

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check LINK_DETAILS annotations
        link_details = self.session.query(Annotation).join(AnnotationCnf,ExplicitRef).filter(AnnotationCnf.name == "LINK_DETAILS_CH2",
                                                                                             ExplicitRef.explicit_ref == "S2A_20200616103316026031").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "S2A_20200616103316026031"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
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
                "name": "isp_status",
                "type": "text",
                "value": "INCOMPLETE"
            },
            {
                "name": "acquisition_status",
                "type": "text",
                "value": "INCOMPLETE"
            }
        ]

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 57

        # Check PLAYBACK_VALIDITY events
        playback_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_%")).all()

        assert len(playback_validity_events) == 2

        definite_playback_validity_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_20",
                                                                                   Event.start == "2020-06-16T10:48:14.163529",
                                                                                   Event.stop == "2020-06-16T10:56:03.533806").all()

        assert definite_playback_validity_event1[0].get_structured_values() == [
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },{
                "name": "channel",
                "type": "double",
                "value": "2.0"
            },{
                "name": "vcid",
                "type": "double",
                "value": "20.0"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },{
                "name": "status",
                "type": "text",
                "value": "INCOMPLETE"
            }
        ]

        definite_playback_validity_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_2",
                                                                                   Event.start == "2020-06-16T10:55:39.547585",
                                                                                   Event.stop == "2020-06-16T10:55:59.768667").all()

        assert definite_playback_validity_event2[0].get_structured_values() == [
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },{
                "name": "channel",
                "type": "double",
                "value": "2.0"
            },{
                "name": "vcid",
                "type": "double",
                "value": "2.0"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "SAD"
            },{
                "name": "status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        raw_isp_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY").all()

        assert len(raw_isp_validity_events) == 1

        assert raw_isp_validity_events[0].get_structured_values() == [
            {
                "name": "status",
                "type": "text",
                "value": "INCOMPLETE"
            },{
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },{
                "name": "channel",
                "type": "double",
                "value": "2.0"
            },{
                "name": "vcid",
                "type": "double",
                "value": "20.0"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },{
                "name": "num_packets",
                "type": "double",
                "value": "1341361.0"
            },{
                "name": "num_frames",
                "type": "double",
                "value": "11932267.0"
            },{
                "name": "expected_num_packets",
                "type": "double",
                "value": "0.0"
            },{
                "name": "diff_expected_received",
                "type": "double",
                "value": "-1341361.0"
            },{
                "name": "packet_status",
                "type": "text",
                "value": "MISSING"
            }
        ]

        explicit_refs = self.session.query(ExplicitRef).all()

        assert len(explicit_refs) == 1

        definite_explicit_ref = self.session.query(ExplicitRef).join(ExplicitRefGrp).filter(ExplicitRef.explicit_ref == "S2A_20200616103316026031",
                                                                                    ExplicitRefGrp.name == "STATION_LINK_SESSION_IDs").all()

        assert len(definite_explicit_ref) == 1

    def test_insert_rep_pass_with_hktm(self):
        filename = "S2A_OPER_REP_PASS_E_VGS2_20200616T105621_V20200616T104814_20200616T105621.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check number of sources generated
        sources = self.session.query(Source).all()

        assert len(sources) == 2

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        source = self.session.query(Source).filter(Source.reported_validity_start == "2020-06-16T10:48:14",
                                                   Source.reported_validity_stop == "2020-06-16T10:56:21",
                                                   Source.validity_start == "2020-06-16T09:13:34.933091",
                                                   Source.validity_stop == "2020-06-16T10:56:21.385567").all()

        assert len(source) == 2

        dim_signatures = self.session.query(DimSignature).all()

        # Check number of dim_signatures generated
        assert len(dim_signatures) == 2

        dim_signature = self.session.query(DimSignature).filter(DimSignature.dim_signature == "RECEPTION_S2A").all()

        assert len(dim_signature) == 1

        dim_signature = self.session.query(DimSignature).filter(DimSignature.dim_signature == "ISP_VALIDITY_PROCESSING_COMPLETENESS_S2A").all()

        assert len(dim_signature) == 1

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check LINK_DETAILS annotations
        link_details = self.session.query(Annotation).join(AnnotationCnf,ExplicitRef).filter(AnnotationCnf.name == "LINK_DETAILS_CH1",
                                                                                             ExplicitRef.explicit_ref == "S2A_20200616103316026031").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "S2A_20200616103316026031"
            },
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
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
                "name": "isp_status",
                "type": "text",
                "value": "INCOMPLETE"
            },
            {
                "name": "acquisition_status",
                "type": "text",
                "value": "INCOMPLETE"
            }
        ]

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 186

        # Check PLAYBACK_VALIDITY events
        playback_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_%")).all()

        assert len(playback_validity_events) == 2

        definite_playback_validity_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_4",
                                                                                   Event.start == "2020-06-16T10:48:14.593190",
                                                                                   Event.stop == "2020-06-16T10:56:21.385567").all()

        assert definite_playback_validity_event1[0].get_structured_values() == [
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },{
                "name": "channel",
                "type": "double",
                "value": "1.0"
            },{
                "name": "vcid",
                "type": "double",
                "value": "4.0"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },{
                "name": "status",
                "type": "text",
                "value": "INCOMPLETE"
            }
        ]

        definite_playback_validity_event2 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_VALIDITY_3",
                                                                                   Event.start == "2020-06-16T10:55:27.964884",
                                                                                   Event.stop == "2020-06-16T10:56:16.426891").all()

        assert definite_playback_validity_event2[0].get_structured_values() == [
            {
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },{
                "name": "channel",
                "type": "double",
                "value": "1.0"
            },{
                "name": "vcid",
                "type": "double",
                "value": "3.0"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "HKTM"
            },{
                "name": "status",
                "type": "text",
                "value": "COMPLETE"
            }
        ]

        raw_isp_validity_events = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY").all()

        assert len(raw_isp_validity_events) == 1

        assert raw_isp_validity_events[0].get_structured_values() == [
            {
                "name": "status",
                "type": "text",
                "value": "INCOMPLETE"
            },{
                "name": "downlink_orbit",
                "type": "double",
                "value": "26031.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "reception_station",
                "type": "text",
                "value": "SGS_"
            },{
                "name": "channel",
                "type": "double",
                "value": "1.0"
            },{
                "name": "vcid",
                "type": "double",
                "value": "4.0"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },{
                "name": "num_packets",
                "type": "double",
                "value": "1337607.0"
            },{
                "name": "num_frames",
                "type": "double",
                "value": "11900051.0"
            },{
                "name": "expected_num_packets",
                "type": "double",
                "value": "0.0"
            },{
                "name": "diff_expected_received",
                "type": "double",
                "value": "-1337607.0"
            },{
                "name": "packet_status",
                "type": "text",
                "value": "MISSING"
            }
        ]

        explicit_refs = self.session.query(ExplicitRef).all()

        assert len(explicit_refs) == 1

        definite_explicit_ref = self.session.query(ExplicitRef).join(ExplicitRefGrp).filter(ExplicitRef.explicit_ref == "S2A_20200616103316026031",
                                                                                    ExplicitRefGrp.name == "STATION_LINK_SESSION_IDs").all()

        assert len(definite_explicit_ref) == 1

    #Issues to be fixed in the ingestion
    def test_insert_rep_pass_with_planning(self):

        filename = "S2A_OPER_MPL__NPPF__20200604T120000_20200622T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_MPL_ORBPRE_20200616T030222_20200626T030222_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_MPL_SPSGS__PDMC_20200615T090003_V20200616T090000_20200622T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_PASS_E_VGS2_20200616T105604_V20200616T104814_20200616T105603.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check number of events generated
        events = self.session.query(Event).join(Source).filter(Source.name == "S2A_OPER_REP_PASS_E_VGS2_20200616T105604_V20200616T104814_20200616T105603.EOF").all()

        assert len(events) == 65

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 1

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        source = self.session.query(Source).filter(Source.reported_validity_start == "2020-06-16T10:48:14",
                                                   Source.reported_validity_stop == "2020-06-16T10:56:03",
                                                   Source.validity_start == "2020-06-15T21:02:44.999376",
                                                   Source.validity_stop == "2020-06-16T10:56:03.533806").all()

        assert len(source) == 2

        # Check LINK_DETAILS annotations
        link_details = self.session.query(Annotation).join(AnnotationCnf).filter(AnnotationCnf.name == "LINK_DETAILS_CH2").all()

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "S2A_20200616103316026031",
                "type": "text",
                "name": "session_id"
            },{
                "value": "26031.0",
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
                "value": "INCOMPLETE",
                "type": "text",
                "name": "isp_status"
            },
            {
                "value": "INCOMPLETE",
                "type": "text",
                "name": "acquisition_status"
            }
        ]

        # Check RAW_ISP_VALIDITY events
        raw_isp_validities = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY").all()

        assert len(raw_isp_validities) == 1

        # Check specific RAW_ISP_VALIDITY
        specific_raw_isp_validity1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "RAW_ISP_VALIDITY",
                                                                                 Event.start == "2020-06-16T09:13:34.933091",
                                                                                 Event.stop == "2020-06-16T09:26:01.742068").all()

        assert len(specific_raw_isp_validity1) == 1

        assert specific_raw_isp_validity1[0].get_structured_values() == [
            {
                "name": "status",
                "value": "INCOMPLETE",
                "type": "text"
            },
            {
                "name": "downlink_orbit",
                "value": "26031.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2A",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "SGS_",
                "type": "text"
            },
            {
                "name": "channel",
                "value": "2.0",
                "type": "double"
            },
            {
                "name": "vcid",
                "value": "20.0",
                "type": "double"
            },
            {
                "name": "playback_type",
                "value": "NOMINAL",
                "type": "text"
            },
            {
                "name": "num_packets",
                "value": "1341361.0",
                "type": "double"
            },
            {
                "name": "num_frames",
                "value": "11932267.0",
                "type": "double"
            },
            {
                "name": "expected_num_packets",
                "value": "1347840.0",
                "type": "double"
            },
            {
                "name": "diff_expected_received",
                "value": "6479.0",
                "type": "double"
            },
            {
                "name": "packet_status",
                "value": "MISSING",
                "type": "text"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((24.574467 24.888446, 24.515796 24.666985, 24.457288 24.445502, 24.398955 24.223998, 24.340795 24.002472, 24.282805 23.780925, 24.22497 23.559357, 24.167302 23.337769, 24.109798 23.116161, 24.052455 22.894532, 23.995261 22.672883, 23.938225 22.451215, 23.881346 22.229528, 23.824618 22.007821, 23.768033 21.786095, 23.711599 21.564351, 23.655313 21.342588, 23.59917 21.120807, 23.543164 20.899008, 23.4873 20.677192, 23.431578 20.455357, 23.375991 20.233506, 23.320534 20.011637, 23.265214 19.789751, 23.210027 19.567849, 23.154967 19.34593, 23.100033 19.123995, 23.045227 18.902044, 22.990549 18.680077, 22.93599 18.458095, 22.881551 18.236097, 22.827234 18.014084, 22.773037 17.792056, 22.718954 17.570014, 22.664985 17.347957, 22.611131 17.125885, 22.557391 16.9038, 22.503758 16.6817, 22.450233 16.459587, 22.396818 16.237461, 22.343511 16.015321, 22.290304 15.793168, 22.237201 15.571002, 22.1842 15.348823, 22.131302 15.126632, 22.078498 14.904429, 22.025793 14.682214, 21.973185 14.459987, 21.920673 14.237748, 21.86825 14.015497, 21.815921 13.793236, 21.763683 13.570963, 21.711535 13.348679, 21.659472 13.126385, 21.607497 12.90408, 21.555608 12.681765, 21.503803 12.45944, 21.452079 12.237105, 21.400437 12.01476, 21.348875 11.792405, 21.297393 11.570042, 21.245987 11.347669, 21.194658 11.125287, 21.143405 10.902896, 21.092225 10.680497, 21.041117 10.458089, 20.990082 10.235673, 20.939116 10.01325, 20.88822 9.790818, 20.837391 9.568379, 20.78663 9.345931999999999, 20.735933 9.123478, 20.685302 8.901016, 20.634733 8.678547999999999, 20.584227 8.456073999999999, 20.533781 8.233592, 20.483395 8.011104, 20.433069 7.788611, 20.382799 7.566111, 20.332586 7.343605, 20.282428 7.121094, 20.232326 6.898577, 20.182275 6.676055, 20.132276 6.453528, 20.082329 6.230996, 20.032432 6.008459, 19.982584 5.785917, 19.932781 5.563372, 19.883028 5.340822, 19.83332 5.118268, 19.783655 4.89571, 19.734033 4.673148, 19.684456 4.450584, 19.63492 4.228015, 19.585423 4.005444, 19.535963 3.78287, 19.486546 3.560292, 19.437165 3.337713, 19.387818 3.11513, 19.338505 2.892546, 19.289231 2.66996, 19.239989 2.447371, 19.190776 2.224781, 19.141594 2.002189, 19.092446 1.779596, 19.043326 1.557002, 18.994231 1.334406, 18.945163 1.11181, 18.896126 0.889213, 18.847112 0.666615, 18.798119 0.444018, 18.74915 0.221419, 18.700207 -0.001179, 18.651283 -0.223777, 18.602376 -0.446374, 18.553489 -0.668971, 18.504625 -0.891568, 18.455775 -1.114164, 18.406938 -1.336758, 18.358118 -1.559352, 18.309316 -1.781944, 18.260524 -2.004535, 18.211742 -2.227124, 18.162973 -2.449711, 18.114218 -2.672296, 18.065469 -2.894879, 18.016725 -3.11746, 17.967992 -3.340038, 17.919268 -3.562613, 17.870546 -3.785186, 17.821824 -4.007756, 17.773112 -4.230322, 17.724403 -4.452885, 17.675691 -4.675445, 17.626977 -4.898001, 17.578269 -5.120553, 17.529559 -5.343101, 17.480843 -5.565645, 17.432119 -5.788185, 17.383401 -6.01072, 17.334675 -6.23325, 17.285938 -6.455776, 17.237189 -6.678297, 17.188444 -6.900812, 17.139685 -7.123323, 17.090912 -7.345828, 17.042123 -7.568327, 16.993334 -7.79082, 16.944527 -8.013306999999999, 16.895701 -8.235789, 16.846857 -8.458264, 16.798008 -8.680732000000001, 16.749136 -8.903193999999999, 16.700241 -9.12565, 16.651325 -9.348098, 16.602399 -9.570539, 16.553447 -9.792973, 16.504466 -10.0154, 16.455462 -10.237819, 16.406443 -10.46023, 16.357393 -10.682633, 16.30831 -10.905028, 16.259202 -11.127416, 16.210072 -11.349794, 16.160907 -11.572164, 16.111705 -11.794526, 16.062476 -12.016878, 16.013219 -12.239222, 15.963922 -12.461556, 15.914584 -12.683882, 15.865216 -12.906197, 15.815814 -13.128503, 15.766368 -13.350799, 15.716876 -13.573085, 15.667351 -13.795361, 15.617788 -14.017627, 15.568175 -14.239882, 15.518511 -14.462127, 15.468812 -14.684361, 15.419067 -14.906584, 15.369269 -15.128796, 15.319414 -15.350996, 15.269523 -15.573186, 15.21958 -15.795363, 15.169577 -16.017529, 15.119513 -16.239683, 15.069411 -16.461825, 15.019249 -16.683955, 14.969023 -16.906073, 14.918731 -17.128177, 14.868398 -17.35027, 14.817998 -17.572349, 14.767529 -17.794416, 14.716989 -18.016469, 14.666405 -18.238509, 14.615747 -18.460535, 14.565014 -18.682548, 14.514208 -18.904547, 14.46335 -19.126532, 14.412414 -19.348503, 11.723732 -18.769075, 11.778395 -18.547459, 11.832934 -18.325824, 11.887359 -18.104169, 11.941665 -17.882495, 11.995852 -17.660804, 12.049922 -17.439094, 12.103885 -17.217365, 12.157734 -16.995619, 12.211471 -16.773855, 12.265097 -16.552074, 12.318621 -16.330274, 12.372038 -16.108457, 12.425348 -15.886625, 12.478555 -15.664775, 12.531664 -15.442908, 12.584671 -15.221025, 12.637578 -14.999126, 12.690388 -14.777211, 12.743105 -14.555279, 12.795726 -14.333333, 12.848252 -14.111371, 12.900687 -13.889394, 12.953034 -13.667401, 13.00529 -13.445394, 13.057457 -13.223373, 13.109539 -13.001337, 13.161537 -12.779286, 13.21345 -12.557221, 13.265279 -12.335143, 13.317028 -12.113051, 13.368698 -11.890945, 13.420288 -11.668826, 13.4718 -11.446695, 13.523236 -11.224549, 13.574598 -11.002391, 13.625885 -10.780221, 13.6771 -10.558038, 13.728243 -10.335843, 13.779317 -10.113636, 13.830321 -9.891417000000001, 13.881257 -9.669187000000001, 13.932127 -9.446944, 13.982931 -9.224690000000001, 14.033671 -9.002426, 14.084348 -8.780151, 14.134962 -8.557864, 14.185516 -8.335566999999999, 14.23601 -8.11326, 14.286446 -7.890943, 14.336823 -7.668615, 14.387144 -7.446278, 14.437411 -7.223931, 14.487624 -7.001575, 14.537782 -6.779208, 14.587889 -6.556833, 14.637945 -6.334449, 14.687953 -6.112057, 14.737909 -5.889655, 14.787819 -5.667245, 14.837683 -5.444827, 14.887502 -5.222401, 14.937275 -4.999966, 14.987004 -4.777524, 15.036693 -4.555075, 15.086341 -4.332618, 15.135946 -4.110154, 15.185513 -3.887682, 15.235043 -3.665205, 15.284536 -3.44272, 15.33399 -3.220228, 15.383411 -2.997731, 15.432799 -2.775227, 15.482153 -2.552718, 15.531473 -2.330201, 15.580764 -2.10768, 15.630027 -1.885154, 15.679259 -1.662622, 15.728461 -1.440084, 15.777638 -1.217542, 15.826792 -0.994995, 15.875918 -0.772443, 15.925018 -0.549887, 15.974098 -0.327326, 16.023158 -0.104762, 16.072194 0.117807, 16.121209 0.340379, 16.170207 0.562955, 16.21919 0.785534, 16.268151 1.008117, 16.317096 1.230703, 16.366028 1.453292, 16.41495 1.675883, 16.463852 1.898477, 16.512743 2.121074, 16.561626 2.343672, 16.610502 2.566273, 16.659361 2.788876, 16.708214 3.011481, 16.757063 3.234087, 16.805909 3.456694, 16.854741 3.679303, 16.903571 3.901913, 16.952402 4.124524, 17.001234 4.347135, 17.050054 4.569748, 17.098878 4.792361, 17.147706 5.014973, 17.196539 5.237586, 17.245364 5.460199, 17.294198 5.682812, 17.34304 5.905424, 17.391888 6.128035, 17.440735 6.350647, 17.489594 6.573257, 17.538465 6.795866, 17.587346 7.018473, 17.63623 7.24108, 17.68513 7.463685, 17.734047 7.686287, 17.782976 7.908888, 17.831913 8.131487999999999, 17.880871 8.354085, 17.92985 8.576679, 17.978843 8.799270999999999, 18.02785 9.02186, 18.076882 9.244446999999999, 18.125939 9.467029999999999, 18.175013 9.68961, 18.224106 9.912186999999999, 18.273228 10.13476, 18.322381 10.357329, 18.371552 10.579895, 18.420748 10.802456, 18.469978 11.025014, 18.519242 11.247566, 18.568527 11.470115, 18.617843 11.692659, 18.667197 11.915198, 18.716591 12.137731, 18.766007 12.36026, 18.815461 12.582784, 18.864957 12.805302, 18.914497 13.027813, 18.964062 13.25032, 19.01367 13.472821, 19.063326 13.695315, 19.11303 13.917802, 19.162762 14.140284, 19.212544 14.362759, 19.262377 14.585226, 19.312264 14.807687, 19.362181 15.030141, 19.412154 15.252588, 19.462184 15.475026, 19.51227 15.697457, 19.562392 15.919881, 19.612576 16.142297, 19.662822 16.364704, 19.713126 16.587103, 19.763473 16.809494, 19.813887 17.031877, 19.864368 17.254249, 19.91491 17.476613, 19.965502 17.698969, 20.016165 17.921315, 20.066902 18.143651, 20.117702 18.365978, 20.168559 18.588295, 20.219493 18.810602, 20.270505 19.032899, 20.321585 19.255185, 20.372728 19.477462, 20.423954 19.699728, 20.475264 19.921982, 20.526643 20.144226, 20.578095 20.366459, 20.629635 20.588681, 20.681265 20.81089, 20.732967 21.033089, 20.784749 21.255276, 20.836625 21.47745, 20.888598 21.699612, 20.940645 21.921763, 20.992781 22.143901, 21.045018 22.366026, 21.097358 22.588137, 21.149774 22.810237, 21.202289 23.032324, 21.25491 23.254396, 21.307641 23.476455, 21.360452 23.698501, 21.41337 23.920533, 21.466402 24.142551, 21.51955 24.364554, 21.572781 24.586543, 21.626129 24.808518, 21.679597 25.030478, 21.733188 25.252422, 21.786867 25.474353, 24.574467 24.888446))"
                    }
                ]
            }
        ]

        # Check ISP_GAPs events
        isp_gap_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("ISP_GAP")).all()

        assert len(isp_gap_events) == 3

        # Check definite ISP_GAP
        isp_gap_events = self.session.query(Event).join(Gauge).filter(Gauge.name == "ISP_GAP",
                                                                                 Event.start == "2020-06-16T09:25:50.918525",
                                                                                 Event.stop == "2020-06-16T09:26:01.742068").all()

        assert len(isp_gap_events) == 3

        isp_gap_event = [event for event in isp_gap_events for value in event.eventDoubles if value.value == 2 and value.name == "detector"]

        assert len(isp_gap_event) == 1

        assert isp_gap_event[0].get_structured_values() == [
            {
                "name": "impact",
                "value": "AT_THE_END",
                "type": "text"
            },
            {
                "name": "band",
                "value": "1",
                "type": "text"
            },
            {
                "name": "detector",
                "value": "2.0",
                "type": "double"
            },
            {
                "name": "downlink_orbit",
                "value": "26031.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2A",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "SGS_",
                "type": "text"
            },
            {
                "name": "channel",
                "value": "2.0",
                "type": "double"
            },
            {
                "name": "vcid",
                "value": "20.0",
                "type": "double"
            },
            {
                "name": "playback_type",
                "value": "NOMINAL",
                "type": "text"
            },
            {
                "name": "apid",
                "value": "320.0",
                "type": "double"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((14.559133 -18.708275, 14.485848 -19.028403, 14.412414 -19.348503, 11.723732 -18.769075, 11.802521 -18.449485, 11.881059 -18.129856, 14.559133 -18.708275))"
                    }
                ]
            }
        ]

        # Check PLAYBACKGA_Ps events
        playback_gap_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_GAP")).all()

        assert len(playback_gap_events) == 51

        # Check definite PLAYBACK_GAP
        playback_gap_event1 = self.session.query(Event).join(Gauge).filter(Gauge.name == "PLAYBACK_GAP",
                                                                                 Event.start == "2020-06-16T10:48:23.626966",
                                                                                 Event.stop == "2020-06-16T10:48:23.627164").all()

        assert len(playback_gap_event1) == 1

        assert playback_gap_event1[0].get_structured_values() == [
            {
                "type": "double",
                "name": "downlink_orbit",
                "value": "26031.0"
            },
            {
                "type": "text",
                "name": "satellite",
                "value": "S2A"
            },
            {
                "type": "text",
                "name": "reception_station",
                "value": "SGS_"
            },
            {
                "type": "double",
                "name": "channel",
                "value": "2.0"
            },
            {
                "type": "double",
                "name": "vcid",
                "value": "20.0"
            },
            {
                "type": "text",
                "name": "playback_type",
                "value": "NOMINAL"
            },
            {
                "type": "double",
                "name": "estimated_lost",
                "value": "1.0"
            },
            {
                "type": "double",
                "name": "pre_counter",
                "value": "7487409.0"
            },
            {
                "type": "double",
                "name": "post_counter",
                "value": "7487411.0"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((6.138941 45.590469, 2.531048 46.266423, 2.531048 46.266423, 6.138941 45.590469))"
                    }
                ]
            }
        ]

        # Check PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL events
        isp_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL%")).all()

        assert len(isp_completeness_events) == 8

        # Check definite ISP completeness
        isp_completeness_missing_left = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_%"),
                                                                                 Event.start == "2020-06-16T08:56:08.713671",
                                                                                 Event.stop == "2020-06-16T09:13:34.933091").all()

        assert len(isp_completeness_missing_left) == 1

        assert isp_completeness_missing_left[0].get_structured_values() == [
            {
                "type": "text",
                "value": "MPMSNOBS",
                "name": "start_request"
            },
            {
                "type": "text",
                "value": "MPMSIMID",
                "name": "stop_request"
            },
            {
                "type": "double",
                "value": "26030.0",
                "name": "start_orbit"
            },
            {
                "type": "double",
                "value": "91.5921",
                "name": "start_angle"
            },
            {
                "type": "double",
                "value": "26030.0",
                "name": "stop_orbit"
            },
            {
                "type": "double",
                "value": "202.7681",
                "name": "stop_angle"
            },
            {
                "type": "text",
                "value": "S2A",
                "name": "satellite"
            },
            {
                "type": "text",
                "value": "NOMINAL",
                "name": "record_type"
            },
            {
                "type": "text",
                "value": "NOMINAL",
                "name": "imaging_mode"
            },
            {
                "type": "object",
                "values": [
                    {
                        "type": "double",
                        "value": "0.0",
                        "name": "start_scn_dup"
                    }
                ],
                "name": "parameters"
            },
            {
                "type": "text",
                "value": "TIME_CORRECTED",
                "name": "status_correction"
            },
            {
                "type": "double",
                "value": "-10.472671",
                "name": "delta_start"
            },
            {
                "type": "double",
                "value": "-10.566674",
                "name": "delta_stop"
            },
            {
                "type": "text",
                "value": "MISSING",
                "name": "status"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((100.828454 79.932778, 99.074708 79.86044200000001, 97.346777 79.77912999999999, 95.64696000000001 79.689053, 93.977293 79.590439, 92.33954199999999 79.483527, 90.73520499999999 79.368568, 89.165521 79.245819, 87.631472 79.115544, 86.133791 78.978015, 84.673008 78.833495, 83.249437 78.68225099999999, 81.863202 78.524547, 80.514253 78.360647, 79.20238500000001 78.19080700000001, 77.92725799999999 78.01528, 76.688417 77.834311, 75.4853 77.64814, 74.31726399999999 77.456997, 73.183593 77.261105, 72.083512 77.060681, 71.016201 76.85593, 69.980805 76.647052, 68.976443 76.434236, 68.002218 76.217664, 67.057221 75.99751000000001, 66.14054299999999 75.77394, 65.25127500000001 75.547111, 64.388516 75.31717500000001, 63.551377 75.08427500000001, 62.73898 74.848545, 61.950468 74.610117, 61.184985 74.36911600000001, 60.441721 74.12565600000001, 59.719887 73.879848, 59.018708 73.63179700000001, 58.337434 73.381602, 57.675341 73.129358, 57.031725 72.87515500000001, 56.405911 72.619078, 55.797243 72.361209, 55.205093 72.101624, 54.628855 71.840396, 54.067945 71.577595, 53.521803 71.313287, 52.989889 71.047533, 52.471686 70.780393, 51.966697 70.511923, 51.474443 70.242178, 50.994467 69.97120700000001, 50.52633 69.69906, 50.069608 69.425783, 49.623898 69.15141800000001, 49.18881 68.876009, 48.763973 68.59959499999999, 48.349019 68.322215, 47.943607 68.043904, 47.547417 67.764697, 47.160134 67.48462499999999, 46.781453 67.20372, 46.411086 66.922012, 46.048753 66.639529, 45.694187 66.356298, 45.34713 66.072346, 45.007337 65.787696, 44.67457 65.502374, 44.348602 65.21639999999999, 44.029214 64.92979800000001, 43.716196 64.64258700000001, 43.409347 64.354788, 43.108473 64.06641999999999, 42.813388 63.7775, 42.523911 63.488047, 42.239871 63.198076, 41.961101 62.907604, 41.687443 62.616647, 41.418742 62.325218, 41.154851 62.033333, 40.89562 61.741005, 40.640912 61.448249, 40.390602 61.155074, 40.144563 60.861494, 39.902672 60.567519, 39.66481 60.273162, 39.430864 59.978432, 39.200724 59.68334, 38.974283 59.387896, 38.751438 59.09211, 38.532092 58.79599, 38.316148 58.499545, 38.103514 58.202785, 37.894102 57.905717, 37.687824 57.60835, 37.484599 57.31069, 37.284345 57.012745, 37.086985 56.714523, 36.892443 56.41603, 36.700648 56.117274, 36.511529 55.818259, 36.325017 55.518993, 36.141047 55.219482, 35.959551 54.919731, 35.780464 54.619747, 35.603735 54.319535, 35.429304 54.019099, 35.257116 53.718444, 35.087117 53.417577, 34.919253 53.1165, 34.753473 52.81522, 34.589729 52.51374, 34.427971 52.212064, 34.268153 51.910198, 34.11023 51.608144, 33.954158 51.305908, 33.799895 51.003492, 33.647398 50.700901, 33.496628 50.398138, 33.347545 50.095206, 33.200112 49.79211, 33.054292 49.488852, 32.910049 49.185435, 32.767347 48.881863, 32.626154 48.578138, 32.486436 48.274264, 32.348159 47.970244, 32.211289 47.66608, 32.0758 47.361776, 31.941664 47.057332, 31.808851 46.752754, 31.677334 46.448041, 31.547086 46.143198, 31.41808 45.838226, 31.29029 45.533128, 31.163691 45.227906, 31.038258 44.922562, 30.913969 44.617098, 30.790798 44.311517, 30.668725 44.00582, 30.547726 43.70001, 30.42778 43.394088, 30.308867 43.088056, 30.190965 42.781916, 30.074054 42.475671, 29.958115 42.169321, 29.84313 41.862868, 29.729078 41.556315, 29.615943 41.249662, 29.503705 40.942912, 29.392344 40.636066, 29.281846 40.329126, 29.172197 40.022093, 29.063379 39.714968, 28.955378 39.407753, 28.848177 39.100449, 28.741762 38.793058, 28.636117 38.485581, 28.531229 38.17802, 28.427084 37.870375, 28.323667 37.562648, 28.220965 37.254841, 28.118965 36.946954, 28.017655 36.638989, 27.917021 36.330946, 27.817051 36.022828, 27.717733 35.714635, 27.619056 35.406369, 27.521008 35.098029, 27.423577 34.789619, 27.326752 34.481138, 27.230523 34.172587, 27.134879 33.863969, 27.039805 33.555283, 26.945295 33.246531, 26.85134 32.937714, 26.757929 32.628832, 26.665053 32.319887, 26.572703 32.010879, 26.480869 31.70181, 26.389542 31.392681, 26.298714 31.083491, 26.208375 30.774243, 26.118518 30.464937, 26.029133 30.155573, 25.940213 29.846154, 25.851748 29.536679, 25.763733 29.22715, 25.676158 28.917566, 25.589016 28.60793, 25.5023 28.298242, 25.416001 27.988502, 25.330114 27.678712, 25.24463 27.368871, 25.159543 27.058982, 25.074846 26.749045, 24.99053 26.43906, 24.90659 26.129028, 24.82302 25.81895, 24.739813 25.508826, 24.656964 25.198658, 24.574467 24.888446, 21.786867 25.474353, 21.862285 25.785234, 21.937936 26.096083, 22.013828 26.406902, 22.089964 26.71769, 22.166349 27.028445, 22.242989 27.339169, 22.319883 27.649859, 22.397043 27.960516, 22.474473 28.27114, 22.55218 28.581728, 22.630169 28.892282, 22.708447 29.2028, 22.787018 29.513282, 22.86589 29.823728, 22.945067 30.134137, 23.024557 30.444508, 23.104366 30.75484, 23.1845 31.065134, 23.264966 31.375389, 23.345769 31.685604, 23.426919 31.995778, 23.50842 32.305912, 23.59028 32.616004, 23.672507 32.926053, 23.755107 33.23606, 23.838089 33.546024, 23.921459 33.855944, 24.005226 34.165819, 24.089398 34.475649, 24.173975 34.785434, 24.258971 35.095172, 24.344397 35.404863, 24.43026 35.714507, 24.51657 36.024102, 24.603336 36.333649, 24.690566 36.643145, 24.778271 36.952592, 24.866459 37.261987, 24.95514 37.57133, 25.044325 37.880621, 25.134024 38.189859, 25.224246 38.499043, 25.315003 38.808172, 25.406306 39.117245, 25.498165 39.426262, 25.590593 39.735223, 25.6836 40.044125, 25.777199 40.352969, 25.871402 40.661753, 25.966221 40.970477, 26.06167 41.279139, 26.157761 41.587739, 26.254499 41.896277, 26.351905 42.204752, 26.449994 42.513161, 26.54878 42.821504, 26.64828 43.129781, 26.748507 43.43799, 26.849478 43.74613, 26.951208 44.0542, 27.053714 44.362199, 27.157012 44.670126, 27.261119 44.97798, 27.366055 45.285759, 27.471835 45.593463, 27.57848 45.90109, 27.686008 46.20864, 27.794438 46.51611, 27.903792 46.8235, 28.014089 47.130807, 28.125352 47.438032, 28.237601 47.745172, 28.350859 48.052226, 28.46515 48.359193, 28.580497 48.66607, 28.696916 48.972858, 28.814436 49.279554, 28.933088 49.586155, 29.052897 49.892662, 29.173893 50.199071, 29.296102 50.505381, 29.419555 50.811591, 29.54428 51.117697, 29.670309 51.423699, 29.797674 51.729594, 29.926408 52.03538, 30.056544 52.341056, 30.188117 52.646618, 30.321164 52.952064, 30.455721 53.257393, 30.591827 53.562601, 30.729522 53.867687, 30.868847 54.172647, 31.009843 54.47748, 31.152555 54.782181, 31.297027 55.086749, 31.443307 55.39118, 31.591442 55.695471, 31.741473 55.99962, 31.893454 56.303624, 32.047445 56.607478, 32.203502 56.911179, 32.361682 57.214723, 32.522044 57.518107, 32.684649 57.821326, 32.849562 58.124377, 33.016848 58.427255, 33.186576 58.729955, 33.358818 59.032474, 33.533646 59.334806, 33.711137 59.636946, 33.891371 59.93889, 34.074431 60.240633, 34.260401 60.542167, 34.449372 60.843488, 34.641436 61.14459, 34.836689 61.445466, 35.035232 61.74611, 35.237168 62.046515, 35.442608 62.346674, 35.651663 62.64658, 35.864442 62.946225, 36.081066 63.245602, 36.301675 63.544701, 36.526402 63.843514, 36.755387 64.142031, 36.988775 64.440242, 37.226719 64.73813800000001, 37.469376 65.035708, 37.716914 65.33293999999999, 37.969506 65.629824, 38.227334 65.926346, 38.490587 66.222495, 38.759464 66.51825599999999, 39.034174 66.813616, 39.314935 67.10856, 39.601975 67.40307199999999, 39.895536 67.697136, 40.195867 67.990734, 40.503233 68.283849, 40.817913 68.57646200000001, 41.140196 68.86855199999999, 41.470389 69.160098, 41.808813 69.451077, 42.155797 69.741469, 42.511689 70.03124699999999, 42.876881 70.320384, 43.251769 70.608852, 43.636769 70.89662199999999, 44.032318 71.183661, 44.438879 71.469937, 44.856941 71.755416, 45.287017 72.040058, 45.729651 72.323826, 46.185417 72.60667599999999, 46.654921 72.888564, 47.138804 73.169443, 47.637743 73.449262, 48.152454 73.727966, 48.683695 74.0055, 49.232266 74.2818, 49.799015 74.556802, 50.384838 74.830437, 50.990684 75.102628, 51.617558 75.37329800000001, 52.26652 75.642359, 52.938693 75.909722, 53.635253 76.17528900000001, 54.357439 76.438959, 55.106603 76.700615, 55.884143 76.96013600000001, 56.691535 77.217394, 57.530331 77.47225, 58.402166 77.724555, 59.308755 77.974149, 60.251896 78.22086, 61.233468 78.464505, 62.25543 78.704885, 63.319818 78.941788, 64.428736 79.174987, 65.58435299999999 79.40423800000001, 66.788887 79.62927999999999, 68.04459300000001 79.84983200000001, 69.353742 80.06559799999999, 70.71860100000001 80.276259, 72.141398 80.481477, 73.62429 80.680892, 75.16932 80.87412500000001, 76.77836600000001 81.060776, 78.453084 81.240424, 80.194834 81.412633, 82.004604 81.57695099999999, 83.882997 81.732901, 85.830066 81.880002, 87.84525600000001 82.017765, 89.92732700000001 82.14569899999999, 92.074271 82.263316, 94.283254 82.370141, 96.550561 82.46571299999999, 100.828454 79.932778))"
                    }
                ]
            }
        ]
        
        isp_completeness_statuses = [event for event in isp_completeness_missing_left if len([value for value in event.eventTexts if value.name == "status" and value.value == "MISSING"]) > 0]

        assert len(isp_completeness_statuses) == 1

        # Check specific ISP completeness
        isp_completeness_1 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_%"),
                                                                                 Event.start == "2020-06-16T09:13:34.933091",
                                                                                 Event.stop == "2020-06-16T09:26:01.742068").all()

        assert len(isp_completeness_1) == 1

        assert isp_completeness_1[0].get_structured_values() == [
            {
                "type": "text",
                "value": "INCOMPLETE",
                "name": "status"
            },
            {
                "type": "double",
                "value": "26031.0",
                "name": "downlink_orbit"
            },
            {
                "type": "text",
                "value": "S2A",
                "name": "satellite"
            },
            {
                "type": "text",
                "value": "SGS_",
                "name": "reception_station"
            },
            {
                "type": "double",
                "value": "2.0",
                "name": "channel"
            },
            {
                "type": "double",
                "value": "20.0",
                "name": "vcid"
            },
            {
                "type": "text",
                "value": "NOMINAL",
                "name": "playback_type"
            },
            {
                "type": "double",
                "value": "26030.0",
                "name": "sensing_orbit"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((24.574467 24.888446, 24.515796 24.666985, 24.457288 24.445502, 24.398955 24.223998, 24.340795 24.002472, 24.282805 23.780925, 24.22497 23.559357, 24.167302 23.337769, 24.109798 23.116161, 24.052455 22.894532, 23.995261 22.672883, 23.938225 22.451215, 23.881346 22.229528, 23.824618 22.007821, 23.768033 21.786095, 23.711599 21.564351, 23.655313 21.342588, 23.59917 21.120807, 23.543164 20.899008, 23.4873 20.677192, 23.431578 20.455357, 23.375991 20.233506, 23.320534 20.011637, 23.265214 19.789751, 23.210027 19.567849, 23.154967 19.34593, 23.100033 19.123995, 23.045227 18.902044, 22.990549 18.680077, 22.93599 18.458095, 22.881551 18.236097, 22.827234 18.014084, 22.773037 17.792056, 22.718954 17.570014, 22.664985 17.347957, 22.611131 17.125885, 22.557391 16.9038, 22.503758 16.6817, 22.450233 16.459587, 22.396818 16.237461, 22.343511 16.015321, 22.290304 15.793168, 22.237201 15.571002, 22.1842 15.348823, 22.131302 15.126632, 22.078498 14.904429, 22.025793 14.682214, 21.973185 14.459987, 21.920673 14.237748, 21.86825 14.015497, 21.815921 13.793236, 21.763683 13.570963, 21.711535 13.348679, 21.659472 13.126385, 21.607497 12.90408, 21.555608 12.681765, 21.503803 12.45944, 21.452079 12.237105, 21.400437 12.01476, 21.348875 11.792405, 21.297393 11.570042, 21.245987 11.347669, 21.194658 11.125287, 21.143405 10.902896, 21.092225 10.680497, 21.041117 10.458089, 20.990082 10.235673, 20.939116 10.01325, 20.88822 9.790818, 20.837391 9.568379, 20.78663 9.345931999999999, 20.735933 9.123478, 20.685302 8.901016, 20.634733 8.678547999999999, 20.584227 8.456073999999999, 20.533781 8.233592, 20.483395 8.011104, 20.433069 7.788611, 20.382799 7.566111, 20.332586 7.343605, 20.282428 7.121094, 20.232326 6.898577, 20.182275 6.676055, 20.132276 6.453528, 20.082329 6.230996, 20.032432 6.008459, 19.982584 5.785917, 19.932781 5.563372, 19.883028 5.340822, 19.83332 5.118268, 19.783655 4.89571, 19.734033 4.673148, 19.684456 4.450584, 19.63492 4.228015, 19.585423 4.005444, 19.535963 3.78287, 19.486546 3.560292, 19.437165 3.337713, 19.387818 3.11513, 19.338505 2.892546, 19.289231 2.66996, 19.239989 2.447371, 19.190776 2.224781, 19.141594 2.002189, 19.092446 1.779596, 19.043326 1.557002, 18.994231 1.334406, 18.945163 1.11181, 18.896126 0.889213, 18.847112 0.666615, 18.798119 0.444018, 18.74915 0.221419, 18.700207 -0.001179, 18.651283 -0.223777, 18.602376 -0.446374, 18.553489 -0.668971, 18.504625 -0.891568, 18.455775 -1.114164, 18.406938 -1.336758, 18.358118 -1.559352, 18.309316 -1.781944, 18.260524 -2.004535, 18.211742 -2.227124, 18.162973 -2.449711, 18.114218 -2.672296, 18.065469 -2.894879, 18.016725 -3.11746, 17.967992 -3.340038, 17.919268 -3.562613, 17.870546 -3.785186, 17.821824 -4.007756, 17.773112 -4.230322, 17.724403 -4.452885, 17.675691 -4.675445, 17.626977 -4.898001, 17.578269 -5.120553, 17.529559 -5.343101, 17.480843 -5.565645, 17.432119 -5.788185, 17.383401 -6.01072, 17.334675 -6.23325, 17.285938 -6.455776, 17.237189 -6.678297, 17.188444 -6.900812, 17.139685 -7.123323, 17.090912 -7.345828, 17.042123 -7.568327, 16.993334 -7.79082, 16.944527 -8.013306999999999, 16.895701 -8.235789, 16.846857 -8.458264, 16.798008 -8.680732000000001, 16.749136 -8.903193999999999, 16.700241 -9.12565, 16.651325 -9.348098, 16.602399 -9.570539, 16.553447 -9.792973, 16.504466 -10.0154, 16.455462 -10.237819, 16.406443 -10.46023, 16.357393 -10.682633, 16.30831 -10.905028, 16.259202 -11.127416, 16.210072 -11.349794, 16.160907 -11.572164, 16.111705 -11.794526, 16.062476 -12.016878, 16.013219 -12.239222, 15.963922 -12.461556, 15.914584 -12.683882, 15.865216 -12.906197, 15.815814 -13.128503, 15.766368 -13.350799, 15.716876 -13.573085, 15.667351 -13.795361, 15.617788 -14.017627, 15.568175 -14.239882, 15.518511 -14.462127, 15.468812 -14.684361, 15.419067 -14.906584, 15.369269 -15.128796, 15.319414 -15.350996, 15.269523 -15.573186, 15.21958 -15.795363, 15.169577 -16.017529, 15.119513 -16.239683, 15.069411 -16.461825, 15.019249 -16.683955, 14.969023 -16.906073, 14.918731 -17.128177, 14.868398 -17.35027, 14.817998 -17.572349, 14.767529 -17.794416, 14.716989 -18.016469, 14.666405 -18.238509, 14.615747 -18.460535, 14.565014 -18.682548, 14.514208 -18.904547, 14.46335 -19.126532, 14.412414 -19.348503, 11.723732 -18.769075, 11.778395 -18.547459, 11.832934 -18.325824, 11.887359 -18.104169, 11.941665 -17.882495, 11.995852 -17.660804, 12.049922 -17.439094, 12.103885 -17.217365, 12.157734 -16.995619, 12.211471 -16.773855, 12.265097 -16.552074, 12.318621 -16.330274, 12.372038 -16.108457, 12.425348 -15.886625, 12.478555 -15.664775, 12.531664 -15.442908, 12.584671 -15.221025, 12.637578 -14.999126, 12.690388 -14.777211, 12.743105 -14.555279, 12.795726 -14.333333, 12.848252 -14.111371, 12.900687 -13.889394, 12.953034 -13.667401, 13.00529 -13.445394, 13.057457 -13.223373, 13.109539 -13.001337, 13.161537 -12.779286, 13.21345 -12.557221, 13.265279 -12.335143, 13.317028 -12.113051, 13.368698 -11.890945, 13.420288 -11.668826, 13.4718 -11.446695, 13.523236 -11.224549, 13.574598 -11.002391, 13.625885 -10.780221, 13.6771 -10.558038, 13.728243 -10.335843, 13.779317 -10.113636, 13.830321 -9.891417000000001, 13.881257 -9.669187000000001, 13.932127 -9.446944, 13.982931 -9.224690000000001, 14.033671 -9.002426, 14.084348 -8.780151, 14.134962 -8.557864, 14.185516 -8.335566999999999, 14.23601 -8.11326, 14.286446 -7.890943, 14.336823 -7.668615, 14.387144 -7.446278, 14.437411 -7.223931, 14.487624 -7.001575, 14.537782 -6.779208, 14.587889 -6.556833, 14.637945 -6.334449, 14.687953 -6.112057, 14.737909 -5.889655, 14.787819 -5.667245, 14.837683 -5.444827, 14.887502 -5.222401, 14.937275 -4.999966, 14.987004 -4.777524, 15.036693 -4.555075, 15.086341 -4.332618, 15.135946 -4.110154, 15.185513 -3.887682, 15.235043 -3.665205, 15.284536 -3.44272, 15.33399 -3.220228, 15.383411 -2.997731, 15.432799 -2.775227, 15.482153 -2.552718, 15.531473 -2.330201, 15.580764 -2.10768, 15.630027 -1.885154, 15.679259 -1.662622, 15.728461 -1.440084, 15.777638 -1.217542, 15.826792 -0.994995, 15.875918 -0.772443, 15.925018 -0.549887, 15.974098 -0.327326, 16.023158 -0.104762, 16.072194 0.117807, 16.121209 0.340379, 16.170207 0.562955, 16.21919 0.785534, 16.268151 1.008117, 16.317096 1.230703, 16.366028 1.453292, 16.41495 1.675883, 16.463852 1.898477, 16.512743 2.121074, 16.561626 2.343672, 16.610502 2.566273, 16.659361 2.788876, 16.708214 3.011481, 16.757063 3.234087, 16.805909 3.456694, 16.854741 3.679303, 16.903571 3.901913, 16.952402 4.124524, 17.001234 4.347135, 17.050054 4.569748, 17.098878 4.792361, 17.147706 5.014973, 17.196539 5.237586, 17.245364 5.460199, 17.294198 5.682812, 17.34304 5.905424, 17.391888 6.128035, 17.440735 6.350647, 17.489594 6.573257, 17.538465 6.795866, 17.587346 7.018473, 17.63623 7.24108, 17.68513 7.463685, 17.734047 7.686287, 17.782976 7.908888, 17.831913 8.131487999999999, 17.880871 8.354085, 17.92985 8.576679, 17.978843 8.799270999999999, 18.02785 9.02186, 18.076882 9.244446999999999, 18.125939 9.467029999999999, 18.175013 9.68961, 18.224106 9.912186999999999, 18.273228 10.13476, 18.322381 10.357329, 18.371552 10.579895, 18.420748 10.802456, 18.469978 11.025014, 18.519242 11.247566, 18.568527 11.470115, 18.617843 11.692659, 18.667197 11.915198, 18.716591 12.137731, 18.766007 12.36026, 18.815461 12.582784, 18.864957 12.805302, 18.914497 13.027813, 18.964062 13.25032, 19.01367 13.472821, 19.063326 13.695315, 19.11303 13.917802, 19.162762 14.140284, 19.212544 14.362759, 19.262377 14.585226, 19.312264 14.807687, 19.362181 15.030141, 19.412154 15.252588, 19.462184 15.475026, 19.51227 15.697457, 19.562392 15.919881, 19.612576 16.142297, 19.662822 16.364704, 19.713126 16.587103, 19.763473 16.809494, 19.813887 17.031877, 19.864368 17.254249, 19.91491 17.476613, 19.965502 17.698969, 20.016165 17.921315, 20.066902 18.143651, 20.117702 18.365978, 20.168559 18.588295, 20.219493 18.810602, 20.270505 19.032899, 20.321585 19.255185, 20.372728 19.477462, 20.423954 19.699728, 20.475264 19.921982, 20.526643 20.144226, 20.578095 20.366459, 20.629635 20.588681, 20.681265 20.81089, 20.732967 21.033089, 20.784749 21.255276, 20.836625 21.47745, 20.888598 21.699612, 20.940645 21.921763, 20.992781 22.143901, 21.045018 22.366026, 21.097358 22.588137, 21.149774 22.810237, 21.202289 23.032324, 21.25491 23.254396, 21.307641 23.476455, 21.360452 23.698501, 21.41337 23.920533, 21.466402 24.142551, 21.51955 24.364554, 21.572781 24.586543, 21.626129 24.808518, 21.679597 25.030478, 21.733188 25.252422, 21.786867 25.474353, 24.574467 24.888446))"
                    }
                ]
            }
        ]

        isp_completeness_2 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_%"),
                                                                                 Event.start == "2020-06-16T09:26:01.742068",
                                                                                 Event.stop == "2020-06-16T09:26:48.132674").all()

        assert len(isp_completeness_2) == 1

        # Check PLANNED_PLAYBACK_COMPLETENESS_CHANNEL events
        playback_completeness_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK_COMPLETENESS_CHANNEL%")).all()

        assert len(playback_completeness_events) == 18

        # Check specific playback completeness
        playback_completeness_1 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2"),
                                                                                 Event.start == "2020-06-16T10:33:29.475935",
                                                                                 Event.stop == "2020-06-16T10:44:44.385938").all()

        assert len(playback_completeness_1) == 1

        assert playback_completeness_1[0].get_structured_values() == [
            {
                "type": "text",
                "value": "INCOMPLETE",
                "name": "status"
            },
            {
                "type": "double",
                "value": "26031.0",
                "name": "downlink_orbit"
            },
            {
                "type": "text",
                "value": "S2A",
                "name": "satellite"
            },
            {
                "type": "text",
                "value": "SGS_",
                "name": "reception_station"
            },
            {
                "type": "double",
                "value": "2.0",
                "name": "channel"
            },
            {
                "type": "double",
                "value": "20.0",
                "name": "vcid"
            },
            {
                "type": "text",
                "value": "NOMINAL",
                "name": "playback_type"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((134.315878 76.17735, 133.654014 76.326882, 132.978116 76.474676, 132.287961 76.62069, 131.583275 76.764869, 130.863685 76.907133, 130.128909 77.04741799999999, 129.378814 77.185694, 128.613 77.321865, 127.831198 77.45585699999999, 127.033221 77.58761699999999, 126.218861 77.71708099999999, 125.387809 77.844151, 124.539863 77.96875199999999, 123.674967 78.09084199999999, 122.792847 78.210313, 121.893348 78.327079, 120.976409 78.441073, 120.041987 78.552224, 119.089942 78.66042299999999, 118.120259 78.76558199999999, 117.133071 78.867654, 116.128352 78.966522, 115.106186 79.062093, 114.066766 79.154293, 113.010336 79.243055, 111.937064 79.328259, 110.847259 79.40982, 109.741364 79.48769, 108.619732 79.561761, 107.48282 79.631939, 106.331187 79.698159, 105.165469 79.760367, 103.986253 79.81845300000001, 102.794255 79.87234599999999, 101.590302 79.922016, 100.375182 79.967376, 99.149764 80.00835499999999, 97.914995 80.044909, 96.671881 80.07701900000001, 95.421408 80.104601, 94.164646 80.127617, 92.90271300000001 80.14606999999999, 91.63672200000001 80.15991699999999, 90.367817 80.16912000000001, 89.09716899999999 80.173676, 87.826404 80.16985200000001, 86.555346 80.168888, 85.28652700000001 80.159507, 84.020652 80.145516, 82.758869 80.12692199999999, 81.50231599999999 80.10373, 80.25209099999999 80.075981, 79.009219 80.04375, 77.774762 80.007036, 76.54970400000001 79.96588800000001, 75.334941 79.92039, 74.13136 79.870593, 72.93981599999999 79.816537, 71.761077 79.758295, 70.59578 79.69597899999999, 69.444653 79.62961799999999, 68.30829300000001 79.559288, 67.187178 79.485095, 66.08178700000001 79.407117, 64.992583 79.325413, 63.919925 79.24007, 62.864004 79.151219, 61.825182 79.05889999999999, 60.803659 78.963199, 59.799525 78.864226, 58.81288 78.762068, 57.843852 78.65678800000001, 56.892462 78.548473, 55.958561 78.43724899999999, 55.042226 78.323159, 54.143378 78.20628499999999, 53.261841 78.08672799999999, 52.39746 77.964572, 51.550151 77.839872, 50.71973 77.712705, 49.905857 77.583185, 49.108435 77.45134899999999, 48.327242 77.317269, 47.561967 77.181028, 46.812322 77.042704, 46.078129 76.902338, 45.359112 76.759996, 44.654853 76.615773, 43.965183 76.469702, 43.289828 76.321836, 42.628442 76.172247, 41.980686 76.020999, 41.346364 75.86812399999999, 40.725181 75.713672, 40.116718 75.557723, 39.520784 75.40030299999999, 38.937117 75.24145300000001, 38.365383 75.081227, 37.805241 74.91968300000001, 37.256519 74.75684, 36.71894 74.59274000000001, 36.192118 74.42744399999999, 35.675871 74.260975, 35.169971 74.093362, 34.674124 73.924649, 34.188009 73.75488300000001, 33.711489 73.584076, 33.244323 73.41225900000001, 32.786171 73.239484, 32.336871 73.06576800000001, 31.896239 72.891131, 31.464024 72.71560700000001, 31.039931 72.539238, 30.623866 72.36202900000001, 30.215625 72.184003, 29.814914 72.00520299999999, 29.421594 71.825642, 29.035522 71.64533400000001, 28.65649 71.464305, 28.284233 71.28259199999999, 27.918689 71.100195, 27.559692 70.917132, 27.206992 70.73343800000001, 26.860468 70.54912400000001, 26.520013 70.364198, 26.185462 70.178681, 25.856569 69.99260599999999, 25.533308 69.80596799999999, 25.215538 69.61878299999999, 24.903052 69.431078, 24.595743 69.242863, 24.293534 69.054143, 23.996295 68.86493400000001, 23.703799 68.675265, 23.416046 68.485129, 23.13292 68.294539, 22.854248 68.103517, 22.579933 67.91207199999999, 22.309926 67.720206, 22.044123 67.527931, 21.782314 67.335274, 21.524519 67.14222700000001, 21.270644 66.94879899999999, 21.020543 66.755008, 20.774128 66.560864, 20.531369 66.366366, 20.292185 66.17152299999999, 20.056387 65.976359, 19.824002 65.780867, 19.594955 65.585052, 19.369125 65.388931, 19.146428 65.19251199999999, 18.926854 64.99579199999999, 18.710333 64.798779, 18.496704 64.601495, 18.285989 64.40393, 18.078134 64.206092, 17.873037 64.007992, 17.670618 63.809638, 17.47088 63.611028, 17.273765 63.412167, 17.079133 63.213072, 16.887005 63.013739, 16.697339 62.81417, 16.510051 62.614376, 16.325064 62.414365, 16.142392 62.214133, 15.961986 62.013684, 15.783724 61.813034, 15.607623 61.612178, 15.433655 61.411118, 15.261749 61.209863, 15.091829 61.008421, 14.923918 60.806786, 14.757976 60.604964, 14.593896 60.402966, 14.431689 60.20079, 14.27134 59.998437, 14.112789 59.795912, 13.955961 59.593225, 13.800885 59.390371, 13.647527 59.187351, 13.495796 58.984179, 13.345697 58.78085, 13.197222 58.577366, 13.050325 58.373731, 12.904928 58.169954, 8.164374 58.999034, 8.283947 59.206613, 8.404699000000001 59.414109, 8.526723 59.621513, 8.650072 59.828821, 8.774741000000001 60.036034, 8.900696999999999 60.243158, 9.02806 60.450179, 9.156860999999999 60.657098, 9.287032 60.863921, 9.418666 61.07064, 9.551829 61.27725, 9.686524 61.483751, 9.822708 61.69015, 9.960520000000001 61.896432, 10.099994 62.102597, 10.241073 62.30865, 10.383845 62.514585, 10.52839 62.720394, 10.674725 62.926078, 10.822796 63.131643, 10.97276 63.337075, 11.124662 63.54237, 11.278452 63.747536, 11.434215 63.952565, 11.592051 64.157448, 11.751989 64.362185, 11.913967 64.566784, 12.078163 64.771227, 12.244633 64.97551199999999, 12.413338 65.179644, 12.584364 65.383617, 12.757828 65.587419, 12.93378 65.791048, 13.112146 65.994516, 13.293134 66.1978, 13.476809 66.400898, 13.66315 66.603814, 13.852241 66.806543, 14.044227 67.00906999999999, 14.239177 67.21139100000001, 14.43701 67.41351899999999, 14.637966 67.615431, 14.842127 67.81712, 15.049491 68.018591, 15.260144 68.219838, 15.474263 68.420844, 15.691941 68.62160299999999, 15.9131 68.82212800000001, 16.138009 69.02239400000001, 16.366775 69.222392, 16.599421 69.42212499999999, 16.836041 69.62158599999999, 17.076849 69.820757, 17.321963 70.019628, 17.571329 70.21821199999999, 17.825238 70.416481, 18.083833 70.614424, 18.347173 70.81204, 18.615361 71.00932400000001, 18.88866 71.20625099999999, 19.167222 71.40281, 19.451027 71.599012, 19.740392 71.794826, 20.03551 71.99023699999999, 20.336485 72.18523999999999, 20.643438 72.379831, 20.956693 72.573978, 21.276448 72.76766600000001, 21.602728 72.960904, 21.935889 73.153657, 22.276187 73.345904, 22.623784 73.537637, 22.978832 73.728847, 23.341734 73.919498, 23.712746 74.10956899999999, 24.091956 74.29906200000001, 24.479773 74.48793999999999, 24.876535 74.676174, 25.282481 74.863747, 25.697809 75.05065, 26.12302 75.236834, 26.558452 75.422273, 27.004274 75.606961, 27.460965 75.790854, 27.928971 75.973912, 28.408629 76.156109, 28.900204 76.33743200000001, 29.404317 76.51781699999999, 29.921411 76.697226, 30.451759 76.87564500000001, 30.995936 77.05301900000001, 31.554513 77.229293, 32.127953 77.404428, 32.716605 77.578401, 33.321235 77.75113, 33.942406 77.922562, 34.580523 78.092668, 35.236262 78.26137799999999, 35.91034 78.428617, 36.603356 78.594324, 37.315749 78.758467, 38.048434 78.920935, 38.802094 79.081655, 39.577256 79.240577, 40.374684 79.39761, 41.195215 79.55265, 42.039554 79.705611, 42.908191 79.856441, 43.802128 80.004998, 44.722098 80.151178, 45.668673 80.294904, 46.642598 80.436059, 47.644703 80.574504, 48.675657 80.71012, 49.735841 80.842833, 50.826139 80.97246, 51.947111 81.098868, 53.099123 81.221946, 54.28262 81.341553, 55.498095 81.45751199999999, 56.745814 81.56967400000001, 58.025699 81.67794499999999, 59.338049 81.782112, 60.682791 81.88201599999999, 62.059601 81.97752699999999, 63.468098 82.06849200000001, 64.907871 82.15471700000001, 66.378204 82.236045, 67.87801899999999 82.312382, 69.40640399999999 82.383521, 70.962076 82.449309, 72.543476 82.509635, 74.148894 82.56437699999999, 75.776527 82.61337, 77.42428200000001 82.65649999999999, 79.089806 82.693725, 80.770757 82.72490000000001, 82.46456000000001 82.749939, 84.168482 82.768804, 85.879716 82.78146599999999, 87.59653400000001 82.78276, 89.31261499999999 82.78793, 91.028406 82.781775, 92.739851 82.76935, 94.444056 82.750675, 96.138222 82.725821, 97.819678 82.69487599999999, 99.48579100000001 82.657871, 101.134115 82.614895, 102.762479 82.566108, 104.368731 82.511582, 105.95094 82.45142800000001, 107.507443 82.385796, 109.036836 82.31486, 110.537694 82.238714, 112.008914 82.157512, 113.449752 82.071455, 114.859395 81.98067, 116.237246 81.885299, 117.582977 81.78551400000001, 118.89651 81.68151, 120.177579 81.57339399999999, 121.426226 81.461324, 122.6428 81.34549199999999, 123.827469 81.226027, 124.980506 81.103055, 126.102393 80.976731, 127.193818 80.847229, 128.255112 80.714636, 129.286879 80.57908399999999, 130.28995 80.440732, 131.26492 80.299684, 132.212386 80.156038, 133.1331 80.009911, 134.028009 79.86145, 134.897592 79.710711, 135.742588 79.557793, 136.5639 79.402818, 137.362201 79.24586600000001, 138.138096 79.08700399999999, 138.892317 78.926317, 139.625802 78.76392, 140.338971 78.599847, 141.032495 78.434168, 141.707179 78.266975, 142.363629 78.098327, 143.002337 77.928265, 134.315878 76.17735))"
                    }
                ]
            }
        ]

        # Check specific playback completeness
        playback_completeness_2 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2"),
                                                                                 Event.start == "2020-06-16T10:45:04.382112",
                                                                                 Event.stop == "2020-06-16T10:45:06.382112").all()

        assert len(playback_completeness_2) == 1

        assert playback_completeness_2[0].get_structured_values() == [
            {
                "type": "text",
                "value": "RECEIVED",
                "name": "status"
            },
            {
                "type": "double",
                "value": "26031.0",
                "name": "downlink_orbit"
            },
            {
                "type": "text",
                "value": "S2A",
                "name": "satellite"
            },
            {
                "type": "text",
                "value": "SGS_",
                "name": "reception_station"
            },
            {
                "type": "double",
                "value": "2.0",
                "name": "channel"
            },
            {
                "type": "double",
                "value": "2.0",
                "name": "vcid"
            },
            {
                "type": "text",
                "value": "SAD",
                "name": "playback_type"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((12.050685 56.924968, 7.461295 57.732065, 7.461295 57.732065, 12.050685 56.924968))"
                    }
                ]
            }
        ]

        
    def test_insert_rep_pass_no_data(self):
        filename = "S2A_OPER_REP_PASS_E_NO_DATA.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check number of events generated
        events = self.session.query(Event).all()

        assert len(events) == 0

        # Check number of annotations generated
        annotations = self.session.query(Annotation).all()

        assert len(annotations) == 0

        # Check that the validity period of the input has taken into consideration the MSI sensing received
        source = self.session.query(Source).filter(Source.reported_validity_start == "2020-06-16T10:48:14",
                                                   Source.reported_validity_stop == "2020-06-16T10:56:21",
                                                   Source.validity_start == "2020-06-16T10:48:14",
                                                   Source.validity_stop == "2020-06-16T10:56:21").all()

        assert len(source) == 1

    #Issues to be fixed in the ingestion
    def test_insert_rep_pass_planning_with_2_playbacks_same_orbit(self):

        filename = "S2A_OPER_MPL__NPPF_2_playbacks_same_orbit.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_MPL_ORBPRE_2_playbacks_same_orbit.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_MPL_SPSGS__PDMC_2_playbacks_same_orbit.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_OPER_REP_PASS_E_VGS2_2_playbacks_same_orbit.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check PLAYBACK_VALIDITY events
        playback_validity_20_events = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLAYBACK_VALIDITY_20")).all()

        assert len(playback_validity_20_events) == 1

        # Check link with planned playbacks
        planned_playback_events = self.query_eboa.get_linking_events(event_uuids = {"filter": str(playback_validity_20_events[0].event_uuid), "op": "=="}, link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="})

        assert len(planned_playback_events["linking_events"]) == 2

        
