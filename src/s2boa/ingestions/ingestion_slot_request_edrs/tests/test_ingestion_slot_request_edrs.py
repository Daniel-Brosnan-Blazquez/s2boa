"""
Automated tests for the ingestion of the SRA_EDRS files

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

    def test_sra_edrs_only(self):

        filename = "S2__OPER_SRA_EDRS_A_PDMC_20180720T030000_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_slot_request_edrs.ingestion_slot_request_edrs", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 2

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              reported_validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T03:00:00", "op": "=="}],
                                                      dim_signatures = {"filter": "SLOT_REQUEST_EDRS_EDRS-A", "op": "=="},
                                              processors = {"filter": "ingestion_slot_request_edrs.py", "op": "like"},
                                              names = {"filter": "S2__OPER_SRA_EDRS_A_PDMC_20180720T030000_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              reported_validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T03:00:00", "op": "=="}],
                                                      dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                              processors = {"filter": "ingestion_slot_request_edrs.py", "op": "like"},
                                              names = {"filter": "S2__OPER_SRA_EDRS_A_PDMC_20180720T030000_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 3

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "SLOT_REQUEST_EDRS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "L20180608110336202000111"
            },{
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },{
                "name": "orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "status",
                "type": "text",
                "value": "NO_MATCHED_PLAYBACK"
            }
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "L20180608110336202000111"
            },{
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },{
                "name": "orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "status",
                "type": "text",
                "value": "NO_MATCHED_PLAYBACK"
            }
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "STATION_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "L20180608110336202000111"
            },{
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },{
                "name": "orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "status",
                "type": "text",
                "value": "NO_MATCHED_PLAYBACK"
            }
        ]
        
        #Check explicit_refs
        explicit_refs = self.query_eboa.get_explicit_refs()

        assert len(explicit_refs) == 1

        #Check a definite explicit_ref
        definite_explicit_ref = self.query_eboa.get_explicit_refs(groups = {"filter": "EDRS_SESSION_IDs", "op": "like"},
                                                          explicit_refs = {"filter": "L20180608110336202000111", "op": "like"})

        assert len(definite_explicit_ref) == 1

    def test_mpl_fs_with_plan(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2__OPER_SRA_EDRS_A_PDMC_20180720T030000_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_slot_request_edrs.ingestion_slot_request_edrs", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 6

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              reported_validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T03:00:00", "op": "=="}],
                                                      dim_signatures = {"filter": "SLOT_REQUEST_EDRS_EDRS-A", "op": "=="},
                                              processors = {"filter": "ingestion_slot_request_edrs.py", "op": "like"},
                                              names = {"filter": "S2__OPER_SRA_EDRS_A_PDMC_20180720T030000_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              reported_validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              validity_start_filters = [{"date": "2018-07-20T03:00:00", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-08-31T23:32:57", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-21T03:00:00", "op": "=="}],
                                                      dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                              processors = {"filter": "ingestion_slot_request_edrs.py", "op": "like"},
                                              names = {"filter": "S2__OPER_SRA_EDRS_A_PDMC_20180720T030000_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "SLOT_REQUEST_EDRS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "L20180608110336202000111"
            },{
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },{
                "name": "orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "status",
                "type": "text",
                "value": "MATCHED_PLAYBACK"
            }
        ]

        #Check explicit_refs
        explicit_refs = self.query_eboa.get_explicit_refs()

        assert len(explicit_refs) == 1

        #Check a definite explicit_ref
        definite_explicit_ref = self.query_eboa.get_explicit_refs(groups = {"filter": "EDRS_SESSION_IDs", "op": "like"},
                                                          explicit_refs = {"filter": "L20180608110336202000111", "op": "like"})

        assert len(definite_explicit_ref) == 1

        planned_playback_events = self.query_eboa.get_events(start_filters = [{"date": "2018-07-21 02:48:22", "op": "=="}],
                                              stop_filters = [{"date": "2018-07-21 03:04:04", "op": "=="}])

        assert len(planned_playback_events) == 1

        planned_playback_correction_events = self.query_eboa.get_events(start_filters = [{"date": "2018-07-21 02:48:27.472821", "op": "=="}],
                                              stop_filters = [{"date": "2018-07-21 03:04:08.957963", "op": "=="}])

        assert len(planned_playback_correction_events) == 1

        planned_playback_event = planned_playback_events[0]

        planned_playback_correction_event = planned_playback_correction_events[0]

        # Check links with PLANNED_PLAYBACK_CORRECTION
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback_event.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(definite_event[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(planned_playback_event.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(definite_event[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "SLOT_REQUEST_EDRS", "op": "like"})

        assert len(link_from_plan) == 1

        assert planned_playback_event.get_structured_values() == [
            {
                "name": "start_request",
                "type": "text",
                "value": "MPMMPNOM"
            },{
                "name": "stop_request",
                "type": "text",
                "value": "MPMMPSTP"
            },{
                "name": "start_orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "start_angle",
                "type": "double",
                "value": "289.7725"
            },{
                "name": "stop_orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "stop_angle",
                "type": "double",
                "value": "345.8436"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "playback_mean",
                "type": "text",
                "value": "OCP"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },
            {
                "name": "parameters",
                "type": "object",
                "values": [
                    {
                        "name": "MEM_FREE",
                        "type": "double",
                        "value": "1.0"
                    },{
                        "name": "SCN_DUP",
                        "type": "double",
                        "value": "0.0"
                    },{
                        "name": "SCN_RWD",
                        "type": "double",
                        "value": "1.0"
                    }
                ]
            },
            {
                "name": "station_schedule",
                "type": "object",
                "values": [{"name": "station",
                            "type": "text",
                            "value": "EDRS"}]},
            {
                "name": "dfep_schedule",
                "type": "object",
                "values": [{"name": "station",
                            "type": "text",
                            "value": "EDRS"}]}
        ]

        assert planned_playback_correction_event.get_structured_values() == [
            {
                "name": "start_request",
                "type": "text",
                "value": "MPMMPNOM"
            },{
                "name": "stop_request",
                "type": "text",
                "value": "MPMMPSTP"
            },{
                "name": "start_orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "start_angle",
                "type": "double",
                "value": "289.7725"
            },{
                "name": "stop_orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "stop_angle",
                "type": "double",
                "value": "345.8436"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "playback_mean",
                "type": "text",
                "value": "OCP"
            },{
                "name": "playback_type",
                "type": "text",
                "value": "NOMINAL"
            },
            {
                "name": "parameters",
                "type": "object",
                "values": [
                    {
                        "name": "MEM_FREE",
                        "type": "double",
                        "value": "1.0"
                    },{
                        "name": "SCN_DUP",
                        "type": "double",
                        "value": "0.0"
                    },{
                        "name": "SCN_RWD",
                        "type": "double",
                        "value": "1.0"
                    }
                ]
            },
            {
                "name": "status_correction",
                "type": "text",
                "value": "TIME_CORRECTED"
            },
            {
                "name": "delta_start",
                "type": "double",
                "value": "-5.472821"
            },
            {
                "name": "delta_stop",
                "type": "double",
                "value": "-4.957963"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((-45.677055 -68.983492, -45.967779 -68.72183200000001, -46.252304 -68.459745, -46.530844 -68.197247, -46.803605 -67.93435100000001, -47.070783 -67.671071, -47.332566 -67.40742, -47.589134 -67.14341, -47.84066 -66.879052, -48.087308 -66.614357, -48.329266 -66.34934, -48.566663 -66.08400899999999, -48.799639 -65.818371, -49.028333 -65.552437, -49.252879 -65.286215, -49.473407 -65.01971500000001, -49.69004 -64.752944, -49.902897 -64.48590900000001, -50.112093 -64.21862, -50.317737 -63.951083, -50.519936 -63.683305, -50.718792 -63.415292, -50.914401 -63.147051, -51.106859 -62.878589, -51.296256 -62.60991, -51.48268 -62.341022, -51.666227 -62.07193, -51.846983 -61.80264, -52.025009 -61.533156, -52.200381 -61.263482, -52.373171 -60.993624, -52.543449 -60.723585, -52.711285 -60.45337, -52.876742 -60.182983, -53.039886 -59.912429, -53.200775 -59.641711, -53.359471 -59.370833, -53.51603 -59.099799, -53.670506 -58.828612, -53.822955 -58.557276, -53.973426 -58.285793, -54.121971 -58.014168, -54.268639 -57.742403, -54.413498 -57.470503, -54.556571 -57.198468, -54.6979 -56.926303, -54.83753 -56.654009, -54.9755 -56.381588, -55.111851 -56.109044, -55.246622 -55.83638, -55.379851 -55.563596, -55.511572 -55.290696, -55.641823 -55.017681, -55.770637 -54.744555, -55.898047 -54.471318, -56.024086 -54.197974, -56.148785 -53.924523, -56.272175 -53.650968, -56.394285 -53.377311, -56.51516 -53.103555, -56.634816 -52.8297, -56.753277 -52.555748, -56.870567 -52.2817, -56.986713 -52.007559, -57.10174 -51.733325, -57.215671 -51.459, -57.328531 -51.184586, -57.440342 -50.910084, -57.551127 -50.635495, -57.660907 -50.360821, -57.769704 -50.086063, -57.877539 -49.811223, -57.98443 -49.536301, -58.090399 -49.261299, -58.195464 -48.986218, -58.29965 -48.711059, -58.402981 -48.435824, -58.505461 -48.160514, -58.607109 -47.885129, -58.707941 -47.60967, -58.807974 -47.334139, -58.907222 -47.058537, -59.005703 -46.782863, -59.103431 -46.50712, -59.200421 -46.231309, -59.296687 -45.955429, -59.392245 -45.679483, -59.487106 -45.403471, -59.581285 -45.127393, -59.674796 -44.851251, -59.76765 -44.575045, -59.859861 -44.298777, -59.951457 -44.022447, -60.042433 -43.746056, -60.132801 -43.469605, -60.222574 -43.193093, -60.311761 -42.916523, -60.400374 -42.639894, -60.488423 -42.363207, -60.57592 -42.086464, -60.662874 -41.809663, -60.749295 -41.532808, -60.835193 -41.255897, -60.920579 -40.978931, -61.00546 -40.701912, -61.089847 -40.42484, -61.173749 -40.147715, -61.257174 -39.870537, -61.340139 -39.593309, -61.42265 -39.316029, -61.50471 -39.0387, -61.586326 -38.76132, -61.667507 -38.483891, -61.748261 -38.206413, -61.828594 -37.928887, -61.908515 -37.651314, -61.988031 -37.373692, -62.06715 -37.096025, -62.145877 -36.81831, -62.224221 -36.54055, -62.302188 -36.262745, -62.379785 -35.984895, -62.457018 -35.707, -62.533894 -35.429062, -62.610422 -35.15108, -62.686615 -34.873055, -62.762468 -34.594987, -62.837989 -34.316878, -62.913183 -34.038727, -62.988056 -33.760534, -63.062613 -33.4823, -63.13686 -33.204026, -63.210803 -32.925712, -63.284447 -32.647359, -63.357797 -32.368966, -63.430858 -32.090534, -63.503636 -31.812064, -63.576136 -31.533555, -63.648362 -31.255009, -63.72032 -30.976426, -63.792013 -30.697806, -63.863457 -30.419149, -63.934648 -30.140457, -64.005588 -29.861728, -64.076283 -29.582964, -64.146736 -29.304166, -64.21695200000001 -29.025332, -64.286936 -28.746464, -64.356692 -28.467563, -64.42622299999999 -28.188627, -64.49553400000001 -27.909659, -64.564628 -27.630657, -64.633511 -27.351624, -64.702185 -27.072558, -64.770655 -26.79346, -64.83892400000001 -26.51433, -64.906997 -26.23517, -64.974881 -25.955979, -65.042579 -25.676757, -65.11009199999999 -25.397506, -65.17742200000001 -25.118224, -65.24457200000001 -24.838913, -65.311547 -24.559573, -65.37835 -24.280205, -65.44498400000001 -24.000808, -65.51145200000001 -23.721383, -65.577758 -23.44193, -65.64390400000001 -23.162449, -65.709895 -22.882942, -65.775733 -22.603408, -65.841421 -22.323847, -65.906963 -22.044261, -65.97236100000001 -21.764648, -66.03762 -21.485011, -66.10274699999999 -21.205348, -66.16773999999999 -20.92566, -66.232601 -20.645948, -66.297332 -20.366211, -66.36193799999999 -20.086451, -66.42641999999999 -19.806667, -66.490781 -19.52686, -66.555024 -19.247031, -66.619152 -18.967178, -66.683167 -18.687304, -66.747073 -18.407407, -66.81087100000001 -18.127489, -66.874565 -17.84755, -66.93815600000001 -17.56759, -67.001648 -17.287609, -67.065043 -17.007608, -67.128349 -16.727587, -67.191564 -16.447546, -67.254689 -16.167485, -67.317727 -15.887406, -67.38068 -15.607308, -67.443551 -15.327192, -67.506342 -15.047058, -67.56905500000001 -14.766905, -67.631692 -14.486736, -67.69425699999999 -14.206549, -65.07942300000001 -13.634412, -65.013469 -13.91428, -64.947372 -14.194125, -64.881128 -14.473946, -64.814735 -14.753742, -64.748189 -15.033513, -64.681488 -15.313259, -64.61463000000001 -15.592979, -64.547611 -15.872673, -64.480429 -16.15234, -64.41307999999999 -16.43198, -64.345563 -16.711592, -64.27787499999999 -16.991177, -64.21001099999999 -17.270733, -64.14196800000001 -17.550261, -64.073745 -17.82976, -64.005337 -18.109229, -63.936741 -18.388669, -63.867954 -18.668078, -63.798973 -18.947457, -63.729795 -19.226804, -63.660417 -19.50612, -63.590834 -19.785405, -63.521044 -20.064656, -63.451043 -20.343876, -63.380828 -20.623062, -63.310395 -20.902214, -63.239742 -21.181332, -63.168866 -21.460416, -63.097761 -21.739464, -63.026424 -22.018477, -62.95485 -22.297455, -62.883037 -22.576396, -62.81098 -22.8553, -62.738676 -23.134168, -62.66612 -23.412997, -62.593308 -23.691789, -62.520236 -23.970542, -62.446901 -24.249256, -62.373298 -24.52793, -62.299422 -24.806564, -62.225269 -25.085158, -62.150835 -25.363711, -62.076118 -25.642222, -62.001113 -25.920692, -61.925813 -26.199118, -61.850214 -26.477502, -61.774311 -26.755842, -61.6981 -27.034139, -61.621575 -27.312391, -61.544731 -27.590597, -61.467563 -27.868758, -61.390067 -28.146874, -61.312237 -28.424942, -61.234068 -28.702963, -61.155553 -28.980936, -61.076689 -29.258862, -60.997469 -29.536738, -60.917888 -29.814564, -60.83794 -30.092341, -60.757625 -30.370067, -60.67693 -30.647741, -60.595852 -30.925364, -60.514382 -31.202934, -60.432515 -31.480452, -60.350245 -31.757915, -60.267565 -32.035324, -60.184468 -32.312679, -60.100949 -32.589977, -60.016999 -32.86722, -59.932613 -33.144405, -59.847783 -33.421533, -59.762501 -33.698602, -59.676761 -33.975612, -59.590556 -34.252563, -59.503877 -34.529453, -59.416721 -34.806282, -59.329079 -35.083049, -59.24094 -35.359753, -59.152295 -35.636394, -59.063137 -35.912971, -58.973458 -36.189482, -58.883248 -36.465928, -58.792498 -36.742307, -58.701201 -37.018619, -58.609345 -37.294862, -58.516923 -37.571037, -58.423925 -37.847141, -58.33034 -38.123174, -58.23616 -38.399135, -58.141373 -38.675024, -58.045971 -38.950838, -57.949944 -39.226579, -57.853285 -39.502243, -57.755977 -39.777831, -57.65801 -40.053342, -57.559372 -40.328773, -57.46005 -40.604126, -57.360035 -40.879397, -57.259312 -41.154586, -57.157871 -41.429693, -57.055697 -41.704715, -56.952779 -41.979652, -56.849102 -42.254502, -56.744654 -42.529265, -56.63942 -42.803939, -56.533386 -43.078523, -56.426539 -43.353015, -56.318862 -43.627414, -56.210352 -43.90172, -56.100982 -44.175931, -55.990737 -44.450044, -55.879601 -44.724059, -55.767557 -44.997975, -55.654589 -45.271789, -55.540678 -45.5455, -55.425808 -45.819107, -55.30996 -46.092608, -55.193115 -46.366001, -55.075255 -46.639286, -54.95636 -46.912459, -54.83641 -47.185519, -54.715384 -47.458464, -54.593263 -47.731293, -54.470023 -48.004004, -54.345652 -48.276595, -54.220123 -48.549064, -54.093409 -48.821409, -53.965486 -49.093627, -53.83633 -49.365717, -53.705916 -49.637676, -53.574219 -49.909502, -53.441212 -50.181192, -53.306869 -50.452745, -53.171162 -50.724158, -53.034063 -50.995427, -52.895542 -51.266552, -52.75557 -51.537529, -52.614117 -51.808355, -52.47115 -52.079027, -52.326638 -52.349543, -52.180552 -52.6199, -52.032863 -52.890096, -51.883527 -53.160127, -51.732507 -53.429988, -51.579768 -53.699678, -51.42527 -53.969192, -51.268974 -54.238527, -51.110842 -54.50768, -50.95083 -54.776646, -50.788897 -55.045423, -50.624999 -55.314005, -50.45909 -55.582389, -50.291125 -55.850571, -50.121056 -56.118546, -49.948834 -56.38631, -49.774407 -56.653858, -49.597725 -56.921186, -49.418748 -57.18829, -49.237407 -57.455163, -49.053644 -57.721801, -48.867401 -57.988198, -48.678617 -58.254349, -48.487229 -58.520247, -48.293173 -58.785887, -48.096382 -59.051262, -47.896788 -59.316366, -47.69432 -59.581194, -47.488905 -59.845736, -47.280467 -60.109988, -47.068929 -60.373941, -46.85421 -60.637588, -46.636227 -60.900922, -46.414895 -61.163933, -46.190135 -61.426616, -45.961854 -61.688961, -45.729949 -61.950958, -45.494322 -62.212597, -45.25487 -62.473871, -45.011491 -62.734767, -44.764074 -62.995276, -44.512509 -63.255387, -44.256679 -63.515089, -43.996464 -63.774371, -43.731739 -64.03322, -43.462376 -64.291623, -43.188241 -64.54956799999999, -42.909197 -64.807041, -42.6251 -65.06402799999999, -42.335802 -65.320515, -42.041154 -65.576486, -41.741011 -65.831929, -41.435189 -66.08682399999999, -41.123517 -66.34115300000001, -40.805818 -66.5949, -40.481908 -66.848045, -40.151596 -67.10056899999999, -39.814684 -67.352452, -39.470965 -67.603673, -39.120228 -67.854209, -45.677055 -68.983492))"
                    }
                ]
            },
            {
                "name": "station_schedule",
                "type": "object",
                "values": [{"name": "station",
                            "type": "text",
                            "value": "EDRS"}]},
            {
                "name": "dfep_schedule",
                "type": "object",
                "values": [{"name": "station",
                            "type": "text",
                            "value": "EDRS"}]}
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "L20180608110336202000111"
            },{
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },{
                "name": "orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "status",
                "type": "text",
                "value": "MATCHED_PLAYBACK"
            }
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "STATION_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "session_id",
                "type": "text",
                "value": "L20180608110336202000111"
            },{
                "name": "edrs_unit",
                "type": "text",
                "value": "EDRS-A"
            },{
                "name": "orbit",
                "type": "double",
                "value": "16073.0"
            },{
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },{
                "name": "status",
                "type": "text",
                "value": "MATCHED_PLAYBACK"
            }
        ]
