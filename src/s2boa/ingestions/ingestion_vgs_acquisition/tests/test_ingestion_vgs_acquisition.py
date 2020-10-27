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
        source = self.session.query(Source).filter(Source.validity_start == "2020-06-15T21:02:44.999376",
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
        source = self.session.query(Source).filter(Source.validity_start == "2020-06-16T09:13:34.933091",
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
        source = self.session.query(Source).filter(Source.validity_start == "2020-06-15T21:02:44.999376",
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
                                                                                 Event.start == "2020-06-16T10:33:30.475935",
                                                                                 Event.stop == "2020-06-16T10:44:43.385938").all()

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
                        "value": "POLYGON ((134.133839 76.218942, 133.466545 76.368364, 132.78507 76.516023, 132.089118 76.66186, 131.378508 76.80584399999999, 130.652885 76.947895, 129.911922 77.08793900000001, 129.155374 77.22591799999999, 128.383066 77.361789, 127.59462 77.495452, 126.789787 77.626834, 125.968432 77.755888, 125.130295 77.88252900000001, 124.275124 78.006666, 123.402755 78.128224, 122.513146 78.247157, 121.606037 78.363347, 120.681325 78.47671099999999, 119.739014 78.587188, 118.779047 78.69468999999999, 117.80136 78.799111, 116.805993 78.900364, 115.793146 78.998408, 114.762815 79.09311, 113.715169 79.184382, 112.650483 79.272159, 111.569035 79.356358, 110.471088 79.43686700000001, 109.357029 79.51360200000001, 108.227387 79.586524, 107.082578 79.655512, 105.923155 79.720483, 104.749771 79.781378, 103.563124 79.83813600000001, 102.363901 79.890658, 101.152905 79.93887599999999, 99.93104099999999 79.982771, 98.699173 80.022251, 97.458251 80.05725700000001, 96.20929599999999 80.087754, 94.953371 80.11372299999999, 93.691529 80.135093, 92.424896 80.151833, 91.154629 80.163956, 89.88188100000001 80.171423, 88.607882 80.17292, 87.334564 80.167, 86.060565 80.16578699999999, 84.789717 80.154582, 83.522294 80.13872000000001, 82.259427 80.118256, 81.002245 80.093204, 79.751852 80.06358, 78.509303 80.02943, 77.275569 79.990841, 76.05166199999999 79.947819, 74.838503 79.90042, 73.636921 79.848732, 72.447726 79.792817, 71.271704 79.73272, 70.10955 79.668516, 68.961805 79.60032699999999, 67.829126 79.52818499999999, 66.71203 79.452169, 65.61091999999999 79.37238499999999, 64.526177 79.28892, 63.458197 79.201836, 62.407266 79.111217, 61.373499 79.017194, 60.357176 78.919816, 59.358438 78.819166, 58.377324 78.715349, 57.413842 78.60846100000001, 56.468078 78.49856200000001, 55.540001 78.38573599999999, 54.62943 78.27010300000001, 53.736355 78.151718, 52.860677 78.030654, 52.002204 77.907004, 51.160696 77.78086399999999, 50.336063 77.652282, 49.528091 77.521332, 48.736443 77.388116, 47.960943 77.252689, 47.201375 77.11510800000001, 46.457446 76.97545, 45.728787 76.833803, 45.01524 76.690201, 44.316517 76.54470600000001, 43.63223 76.397403, 42.962128 76.248338, 42.30597 76.097555, 41.663445 75.945114, 41.034132 75.791095, 40.417874 75.635518, 39.814377 75.478433, 39.223263 75.319906, 38.64426 75.15998, 38.077149 74.99868499999999, 37.521645 74.836066, 36.977324 74.672194, 36.444058 74.50707800000001, 35.921578 74.34075799999999, 35.40955 74.173286, 34.907704 74.004699, 34.415863 73.835016, 33.933779 73.66427299999999, 33.461072 73.492526, 32.997627 73.319785, 32.54322 73.14607599999999, 32.097571 72.971439, 31.660421 72.79591000000001, 31.231642 72.619499, 30.811021 72.44223100000001, 30.398238 72.264154, 29.993182 72.085275, 29.59568 71.905613, 29.205504 71.725199, 28.822408 71.54406400000001, 28.446309 71.362212, 28.077031 71.179664, 27.714305 70.99645700000001, 27.358027 70.81259799999999, 27.00807 70.6281, 26.664252 70.442986, 26.326339 70.257285, 25.994288 70.07099700000001, 25.667952 69.884137, 25.347111 69.696735, 25.031665 69.50879999999999, 24.721524 69.32033800000001, 24.416548 69.131366, 24.116512 68.941912, 23.821406 68.75197300000001, 23.531109 68.561561, 23.245442 68.370698, 22.964305 68.179394, 22.687642 67.98765299999999, 22.415346 67.795485, 22.147201 67.602919, 21.883221 67.409947, 21.62331 67.21657999999999, 21.36732 67.022835, 21.115152 66.828723, 20.866778 66.634244, 20.622108 66.43940600000001, 20.38096 66.24423400000001, 20.143342 66.048721, 19.909184 65.852874, 19.678368 65.65670799999999, 19.450792 65.460234, 19.22645 65.26344899999999, 19.005269 65.06635900000001, 18.787094 64.86898600000001, 18.571926 64.671325, 18.359717 64.47338000000001, 18.150374 64.27516199999999, 17.943791 64.076684, 17.73998 63.87794, 17.538882 63.678936, 17.340366 63.479689, 17.144424 63.280197, 16.951027 63.080461, 16.760103 62.88049, 16.571541 62.680298, 16.385369 62.479876, 16.201538 62.279231, 16.019939 62.078376, 15.840553 61.877311, 15.663368 61.676036, 15.48833 61.474556, 15.315323 61.272885, 15.144389 61.071017, 14.975484 60.868954, 14.80852 60.666709, 14.643468 60.464282, 14.48033 60.261672, 14.319067 60.058884, 14.159558 59.85593, 14.001855 59.652804, 13.845921 59.449509, 13.691685 59.246052, 13.539108 59.042439, 13.388203 58.838665, 13.238937 58.634734, 13.091207 58.430658, 12.945051 58.226431, 8.197367 59.056559, 8.317546 59.264613, 8.439002 59.472575, 8.561657 59.680452, 8.685651 59.888233, 8.811011000000001 60.095915, 8.937697999999999 60.303503, 9.065747999999999 60.510995, 9.195249 60.718383, 9.326233 60.925664, 9.458602000000001 61.13285, 9.592513 61.339925, 9.728002 61.546888, 9.865043 61.753743, 10.003656 61.960487, 10.143949 62.167113, 10.285961 62.373616, 10.429604 62.580008, 10.575027 62.786275, 10.722284 62.992412, 10.871365 63.198422, 11.022272 63.404307, 11.175138 63.610054, 11.330009 63.81566, 11.486813 64.021134, 11.645686 64.22646400000001, 11.806705 64.43164400000001, 11.969882 64.636674, 12.135197 64.841559, 12.302812 65.046283, 12.472784 65.250843, 12.645059 65.455246, 12.81976 65.659482, 12.996993 65.863542, 13.176793 66.06742300000001, 13.359119 66.271135, 13.544168 66.47465699999999, 13.73201 66.67798500000001, 13.922612 66.88112599999999, 14.116087 67.084069, 14.312573 67.286804, 14.512134 67.48932600000001, 14.714708 67.69164499999999, 14.920533 67.89373999999999, 15.129694 68.095602, 15.342189 68.29723799999999, 15.55812 68.498639, 15.777663 68.699789, 16.000916 68.900682, 16.227803 69.101331, 16.458604 69.301709, 16.693431 69.501807, 16.932314 69.701627, 17.175349 69.90116399999999, 17.422758 70.100397, 17.674668 70.299317, 17.931036 70.497936, 18.192149 70.696224, 18.458166 70.894171, 18.729162 71.091775, 19.005228 71.28903099999999, 19.286647 71.485913, 19.573581 71.68240900000001, 19.866032 71.87852700000001, 20.164299 72.07423900000001, 20.468602 72.26952799999999, 20.779073 72.464386, 21.095806 72.658811, 21.419157 72.852769, 21.749337 73.046245, 22.086407 73.239242, 22.430688 73.43173, 22.782476 73.62368499999999, 23.141978 73.815093, 23.5093 74.00595300000001, 23.88489 74.19622099999999, 24.269024 74.385876, 24.661842 74.574915, 25.063698 74.763306, 25.474987 74.951015, 25.896011 75.138018, 26.3269 75.324316, 26.768221 75.509852, 27.220335 75.69459500000001, 27.683482 75.878534, 28.158068 76.061634, 28.64461 76.243846, 29.14353 76.425134, 29.655006 76.605497, 30.179742 76.78486100000001, 30.718209 76.963185, 31.270774 77.140443, 31.837911 77.31659399999999, 32.420288 77.49157099999999, 33.018444 77.665323, 33.632692 77.837834, 34.263824 78.009019, 34.912463 78.178816, 35.579122 78.347179, 36.264351 78.51405800000001, 36.968977 78.67936, 37.693665 78.843014, 38.438867 79.004985, 39.205454 79.165167, 39.994188 79.32347300000001, 40.805713 79.479829, 41.640627 79.63417099999999, 42.499875 79.786372, 43.384198 79.936335, 44.29413 80.083994, 45.230535 80.229223, 46.194221 80.371898, 47.185851 80.51191300000001, 48.205936 80.64918299999999, 49.255377 80.78354, 50.334803 80.914857, 51.444629 81.043035, 52.585465 81.167922, 53.757883 81.289356, 54.962257 81.407195, 56.198686 81.521339, 57.467627 81.63158300000001, 58.769181 81.737769, 60.103198 81.83977299999999, 61.469549 81.937432, 62.868039 82.030556, 64.298196 82.118985, 65.759175 82.202625, 67.250366 82.281254, 68.77075000000001 82.35471699999999, 70.319029 82.42289599999999, 71.893781 82.485652, 73.49347400000001 82.542811, 75.116275 82.594244, 76.76005600000001 82.639894, 78.422714 82.67959500000001, 80.101871 82.713245, 81.794954 82.74078299999999, 83.499279 82.762162, 85.212096 82.77727899999999, 86.93276899999999 82.778907, 88.651732 82.786906, 90.372398 82.784886, 92.08994199999999 82.77480199999999, 93.801312 82.758443, 95.503677 82.73588599999999, 97.194232 82.70713499999999, 98.87031399999999 82.672263, 100.529487 82.63140799999999, 102.169365 82.584638, 103.787739 82.532045, 105.382647 82.47376199999999, 106.952412 82.409965, 108.495325 82.34073600000001, 110.010002 82.266221, 111.495392 82.186612, 112.950475 82.102046, 114.374386 82.012657, 115.766537 81.918611, 117.12669 81.82011900000001, 118.454363 81.71728299999999, 119.749424 81.610264, 121.012018 81.499251, 122.242255 81.384395, 123.440252 81.26581899999999, 124.60634 81.143672, 125.741202 81.018158, 126.845057 80.889359, 127.918448 80.757412, 128.9621 80.62247499999999, 129.976679 80.484679, 130.962704 80.34411900000001, 131.920874 80.200912, 132.852162 80.05521899999999, 133.757069 79.90710799999999, 134.636305 79.756677, 135.490715 79.604046, 136.321118 79.449321, 137.128067 79.292565, 137.91229 79.133865, 138.674738 78.973341, 139.415937 78.811044, 140.136527 78.647041, 140.837264 78.48141699999999, 141.518936 78.31426, 142.181983 78.14560400000001, 142.827033 77.97551199999999, 134.133839 76.218942))"
                    }
                ]
            }
        ]

        # Check specific playback completeness
        playback_completeness_2 = self.session.query(Event).join(Gauge).filter(Gauge.name.like("PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2"),
                                                                                 Event.start == "2020-06-16T10:45:05.382112",
                                                                                 Event.stop == "2020-06-16T10:45:05.382112").all()

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
                        "value": "POLYGON ((12.088372 56.981678, 7.492329 57.789733, 7.492329 57.789733, 12.088372 56.981678))"
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
        source = self.session.query(Source).filter(Source.validity_start == "2020-06-16T10:48:14",
                                                   Source.validity_stop == "2020-06-16T10:56:21").all()

        assert len(source) == 1
