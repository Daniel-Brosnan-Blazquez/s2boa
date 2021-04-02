"""
Automated tests for the ingestion of the MPL_FS files

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

    def test_mpl_fs_only(self):

        filename = "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_schedule.ingestion_dfep_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 2

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T09:00:00", "op": "=="}],
                                                      reported_validity_stop_filters = [{"date": "2018-07-26T09:00:00", "op": "=="}],
                                                      validity_start_filters = [{"date": "2018-07-20T11:03:27.014", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-26T00:47:15.402", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-20T09:00:10", "op": "=="}],
                                                      dim_signatures = {"filter": "DFEP_SCHEDULE_MPS__S2A", "op": "=="},
                                              processors = {"filter": "ingestion_dfep_schedule.py", "op": "like"},
                                              names = {"filter": "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T09:00:00", "op": "=="}],
                                                      reported_validity_stop_filters = [{"date": "2018-07-26T09:00:00", "op": "=="}],
                                                      validity_start_filters = [{"date": "2018-07-20T11:03:27.014", "op": "=="}],
                                                      validity_stop_filters = [{"date": "2018-07-26T00:47:15.402", "op": "=="}],
                                                      generation_time_filters = [{"date": "2018-07-20T09:00:10", "op": "=="}],
                                                      dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                                      processors = {"filter": "ingestion_dfep_schedule.py", "op": "like"},
                                                      names = {"filter": "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        #Check events
        events = self.query_eboa.get_events()

        assert len(events) == 2

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "station",
                "type": "text",
                "value": "MPS_"
            }
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "station",
                "type": "text",
                "value": "MPS_"
            },{
                "name": "playback_mean",
                "type": "text",
                "value": "XBAND"
            }
        ]

    def test_mpl_fs_with_plan(self):

        filename = "S2A_NPPF.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_schedule.ingestion_dfep_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 6

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T09:00:00", "op": "=="}],
                                                      reported_validity_stop_filters = [{"date": "2018-07-26T09:00:00", "op": "=="}],
                                                      validity_start_filters = [{"date": "2018-07-20T11:03:27.014", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-26T00:47:15.402", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-20T09:00:10", "op": "=="}],
                                                      dim_signatures = {"filter": "DFEP_SCHEDULE_MPS__S2A", "op": "=="},
                                              processors = {"filter": "ingestion_dfep_schedule.py", "op": "like"},
                                              names = {"filter": "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T09:00:00", "op": "=="}],
                                                      reported_validity_stop_filters = [{"date": "2018-07-26T09:00:00", "op": "=="}],
                                                      validity_start_filters = [{"date": "2018-07-20T11:03:27.014", "op": "=="}],
                                                      validity_stop_filters = [{"date": "2018-07-26T00:47:15.402", "op": "=="}],
                                                      generation_time_filters = [{"date": "2018-07-20T09:00:10", "op": "=="}],
                                                      dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                                      processors = {"filter": "ingestion_dfep_schedule.py", "op": "like"},
                                                      names = {"filter": "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1
        
        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "station",
                "type": "text",
                "value": "MPS_"
            }
        ]

        planned_playback_events = self.query_eboa.get_events(start_filters = [{"date": "2018-07-21 10:35:27.430000", "op": "=="}],
                                              stop_filters = [{"date": "2018-07-21 10:37:03.431000", "op": "=="}])

        assert len(planned_playback_events) == 1

        planned_playback_correction_events = self.query_eboa.get_events(start_filters = [{"date": "2018-07-21 10:35:32.524661", "op": "=="}],
                                              stop_filters = [{"date": "2018-07-21 10:37:08.530863", "op": "=="}])

        assert len(planned_playback_correction_events) == 1

        planned_playback_event = planned_playback_events[0]

        planned_playback_correction_event = planned_playback_correction_events[0]

        # Check links with PLANNED_PLAYBACK
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback_event.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(definite_event[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(planned_playback_event.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(definite_event[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "DFEP_SCHEDULE", "op": "like"})

        assert len(link_from_plan) == 1

        #Check new value
        assert planned_playback_event.get_structured_values() == [
            {
                'name': 'start_request',
                'type': 'text',
                'value': 'MPMMPNOM'
            },{
                'name': 'stop_request',
                'type': 'text',
                'value': 'MPMMPSTP'
            },{
                'name': 'start_orbit',
                'type': 'double',
                'value': '16078.0'
            },{
                'name': 'start_angle',
                'type': 'double',
                'value': '159.7552'
            },{
                'name': 'stop_orbit',
                'type': 'double',
                'value': '16078.0'
            },{
                'name': 'stop_angle',
                'type': 'double',
                'value': '165.5371'
            },{
                'name': 'satellite',
                'type': 'text',
                'value': 'S2A'
            },{
                'name': 'playback_mean',
                'type': 'text',
                'value': 'XBAND'
            },{
                'name': 'playback_type',
                'type': 'text',
                'value': 'NOMINAL'
            },{
                'name': 'parameters',
                'type': 'object',
                'values': [
                    {
                        'name': 'MEM_FREE',
                        'type': 'double',
                        'value': '1.0'
                    },{
                        'name': 'SCN_DUP',
                        'type': 'double',
                        'value': '0.0'
                    },{
                        'name': 'SCN_RWD',
                        'type': 'double',
                        'value': '1.0'
                    }
                ]
            }
        ]

        #Check new value
        assert planned_playback_correction_event.get_structured_values() == [
            {
                'name': 'start_request',
                'type': 'text',
                'value': 'MPMMPNOM'
            },{
                'name': 'stop_request',
                'type': 'text',
                'value': 'MPMMPSTP'
            },{
                'name': 'start_orbit',
                'type': 'double',
                'value': '16078.0'
            },{
                'name': 'start_angle',
                'type': 'double',
                'value': '159.7552'
            },{
                'name': 'stop_orbit',
                'type': 'double',
                'value': '16078.0'
            },{
                'name': 'stop_angle',
                'type': 'double',
                'value': '165.5371'
            },{
                'name': 'satellite',
                'type': 'text',
                'value': 'S2A'
            },{
                'name': 'playback_mean',
                'type': 'text',
                'value': 'XBAND'
            },{
                'name': 'playback_type',
                'type': 'text',
                'value': 'NOMINAL'
            },{
                'name': 'parameters',
                'type': 'object',
                'values': [
                    {
                        'name': 'MEM_FREE',
                        'type': 'double',
                        'value': '1.0'
                    },{
                        'name': 'SCN_DUP',
                        'type': 'double',
                        'value': '0.0'
                    },{
                        'name': 'SCN_RWD',
                        'type': 'double',
                        'value': '1.0'
                    }
                ]
            },{
                'name': 'status_correction',
                'type': 'text',
                'value': 'TIME_CORRECTED'
            },{
                'name': 'delta_start',
                'type': 'double',
                'value': '-5.094661'
            },{
                'name': 'delta_stop',
                'type': 'double',
                'value': '-5.099863'
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((3.087733 19.617144, 3.03354 19.398794, 2.979473 19.180427, 2.925532 18.962046, 2.871711 18.743648, 2.818006 18.525236, 2.764421 18.306809, 2.710955 18.088367, 2.657601 17.86991, 2.604359 17.651439, 2.551231 17.432954, 2.498216 17.214455, 2.445304 16.995942, 2.392502 16.777416, 2.339807 16.558876, 2.287218 16.340323, 2.234727 16.121758, 2.18234 15.903179, 2.130056 15.684588, 2.07787 15.465984, 2.025779 15.247368, 1.973786 15.028741, 1.921889 14.810101, 1.870084 14.59145, 1.818371 14.372787, 1.766751 14.154113, 1.715221 13.935428, -0.889919 14.504954, -0.840883 14.723846, -0.791795 14.942729, -0.742651 15.161606, -0.6934630000000001 15.380475, -0.6442329999999999 15.599338, -0.594946 15.818193, -0.5456 16.037039, -0.49621 16.255879, -0.446769 16.47471, -0.397265 16.693533, -0.347696 16.912347, -0.298088 17.131154, -0.248416 17.349952, -0.198676 17.568741, -0.148871 17.787521, -0.099021 18.006292, -0.049098 18.225054, 0.000897 18.443806, 0.050955 18.662549, 0.10107 18.881283, 0.151262 19.100006, 0.201533 19.318719, 0.251863 19.537422, 0.302264 19.756115, 0.352747 19.974797, 0.403314 20.193468, 3.087733 19.617144))"
                    }
                ]
            }
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "station",
                "type": "text",
                "value": "MPS_"
            },{
                "name": "playback_mean",
                "type": "text",
                "value": "XBAND"
            }
        ]

    def test_mpl_fs_with_plan_at_latest_position(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_dfep_schedule.ingestion_dfep_schedule", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        filename = "S2A_NPPF_2.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        exit_status = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert len([item for item in exit_status if item["status"] != eboa_engine.exit_codes["OK"]["status"]]) == 0

        #Check sources
        sources = self.query_eboa.get_sources()

        assert len(sources) == 6

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T09:00:00", "op": "=="}],
                                                      reported_validity_stop_filters = [{"date": "2018-07-26T09:00:00", "op": "=="}],
                                                      validity_start_filters = [{"date": "2018-07-20T11:03:27.014", "op": "=="}],
                                              validity_stop_filters = [{"date": "2018-07-26T00:47:15.402", "op": "=="}],
                                              generation_time_filters = [{"date": "2018-07-20T09:00:10", "op": "=="}],
                                                      dim_signatures = {"filter": "DFEP_SCHEDULE_MPS__S2A", "op": "=="},
                                              processors = {"filter": "ingestion_dfep_schedule.py", "op": "like"},
                                              names = {"filter": "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1

        definite_source = self.query_eboa.get_sources(reported_validity_start_filters = [{"date": "2018-07-20T09:00:00", "op": "=="}],
                                                      reported_validity_stop_filters = [{"date": "2018-07-26T09:00:00", "op": "=="}],
                                                      validity_start_filters = [{"date": "2018-07-20T11:03:27.014", "op": "=="}],
                                                      validity_stop_filters = [{"date": "2018-07-26T00:47:15.402", "op": "=="}],
                                                      generation_time_filters = [{"date": "2018-07-20T09:00:10", "op": "=="}],
                                                      dim_signatures = {"filter": "COMPLETENESS_NPPF_S2A", "op": "=="},
                                                      processors = {"filter": "ingestion_dfep_schedule.py", "op": "like"},
                                                      names = {"filter": "S2A_OPER_MPL_FSMPS__PDMC_20180719T090010_RIPPED.EOF", "op": "like"})

        assert len(definite_source) == 1
        
        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "station",
                "type": "text",
                "value": "MPS_"
            }
        ]

        planned_playback_events = self.query_eboa.get_events(start_filters = [{"date": "2018-07-21 10:35:27.430000", "op": "=="}],
                                              stop_filters = [{"date": "2018-07-21 10:37:03.431000", "op": "=="}])

        assert len(planned_playback_events) == 1

        planned_playback_event = planned_playback_events[0]

        # Check links with PLANNED_PLAYBACK
        link_to_plan = self.query_eboa.get_event_links(event_uuid_links = {"filter": [str(planned_playback_event.event_uuid)], "op": "in"},
                                                    event_uuids = {"filter": [str(definite_event[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "PLANNED_PLAYBACK", "op": "like"})

        assert len(link_to_plan) == 1

        link_from_plan = self.query_eboa.get_event_links(event_uuids = {"filter": [str(planned_playback_event.event_uuid)], "op": "in"},
                                                    event_uuid_links = {"filter": [str(definite_event[0].event_uuid)], "op": "in"},
                                                    link_names = {"filter": "DFEP_SCHEDULE", "op": "like"})

        assert len(link_from_plan) == 1

        #Check new value
        assert planned_playback_event.get_structured_values() == [
            {
                'name': 'start_request',
                'type': 'text',
                'value': 'MPMMPNOM'
            },{
                'name': 'stop_request',
                'type': 'text',
                'value': 'MPMMPSTP'
            },{
                'name': 'start_orbit',
                'type': 'double',
                'value': '16078.0'
            },{
                'name': 'start_angle',
                'type': 'double',
                'value': '159.7552'
            },{
                'name': 'stop_orbit',
                'type': 'double',
                'value': '16078.0'
            },{
                'name': 'stop_angle',
                'type': 'double',
                'value': '165.5371'
            },{
                'name': 'satellite',
                'type': 'text',
                'value': 'S2A'
            },{
                'name': 'playback_mean',
                'type': 'text',
                'value': 'XBAND'
            },{
                'name': 'playback_type',
                'type': 'text',
                'value': 'NOMINAL'
            },{
                'name': 'parameters',
                'type': 'object',
                'values': [
                    {
                        'name': 'MEM_FREE',
                        'type': 'double',
                        'value': '1.0'
                    },{
                        'name': 'SCN_DUP',
                        'type': 'double',
                        'value': '0.0'
                    },{
                        'name': 'SCN_RWD',
                        'type': 'double',
                        'value': '1.0'
                    }
                ]
            }
        ]

        #Check definite event
        definite_event = self.query_eboa.get_events(gauge_names = {"filter": "DFEP_SCHEDULE_COMPLETENESS", "op": "like"})

        assert definite_event[0].get_structured_values() == [
            {
                "name": "orbit",
                "type": "double",
                "value": "16078.0"
            },
            {
                "name": "satellite",
                "type": "text",
                "value": "S2A"
            },
            {
                "name": "station",
                "type": "text",
                "value": "MPS_"
            },{
                "name": "playback_mean",
                "type": "text",
                "value": "XBAND"
            }
        ]
