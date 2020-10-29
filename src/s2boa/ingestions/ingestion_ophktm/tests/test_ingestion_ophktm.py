"""
Automated tests for the ingestion of the REP_OPHKTM files

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

class TestDhus(unittest.TestCase):
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

    def test_rep_ophktm(self):

        filename = "S2B_OPER_REP_OPHKTM_VGS2_20201015T131302_V20201015T125641_20201015T125641.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_ophktm.ingestion_ophktm", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

    
    
    def test_insert_rep_pass_with_planning(self):

        filename = "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_nppf.ingestion_nppf", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_station_schedule.ingestion_station_schedule", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        filename = "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_vgs_acquisition.ingestion_vgs_acquisition", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        # Check number of events generated by specific source
        events = self.query_eboa.get_events(sources = {"filter": "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF", "op": "=="})

        assert len(events) == 47

        # Check number of sources generated by specific source
        sources = self.query_eboa.get_sources(names = {"filter": "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF", "op": "=="})

        assert len(sources) == 3

        # Check number of annotations generated by specific source
        annotations = self.query_eboa.get_annotations(sources = {"filter": "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF", "op": "=="})

        assert len(annotations) == 0

        # Check numbers of events generated by specific source and gauge name
        planned_playback_corrections = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "=="},
                                                                  sources = {"filter": "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF", "op": "=="})

        assert len(planned_playback_corrections) == 9

        # Check numbers of events generated by specific source and gauge name
        planned_playback_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK_COMPLETENESS%", "op": "like"},
                                                                   sources = {"filter": "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF", "op": "=="})

        assert len(planned_playback_completeness) == 15

        # Check production playback completeness
        planned_playback_completeness = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK_COMPLETENESS%", "op": "like"},
                                                                   sources = {"filter": "S2B_OPER_MPL_ORBPRE_20201015T030112_20201025T030112_0001.EOF", "op": "=="},
                                                                   start_filters = [{"date": "2020-10-15T12:00:00", "op": ">"}],
                                                                   stop_filters = [{"date": "2020-10-15T013:00:00", "op": "<"}])

        assert len(planned_playback_completeness) == 4

        # Check number of linked events
        planned_playback_correction = planned_playback_corrections[0]
        linked_events = self.query_eboa.get_linked_events(event_uuids = {"filter": [str(planned_playback_correction.event_uuid)], "op": "in"})

        assert len(linked_events) == 2

        ###
        # Check number of events generated by specific source
        events = self.query_eboa.get_events(sources = {"filter": "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF", "op": "=="})

        assert len(events) == 13

        # Check number of sources generated by specific source
        sources = self.query_eboa.get_sources(names = {"filter": "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF", "op": "=="})

        assert len(sources) == 1

        # Check number of annotations generated by specific source
        annotations = self.query_eboa.get_annotations(sources = {"filter": "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF", "op": "=="})

        assert len(annotations) == 0

        
        # Check numbers of events generated by specific source and gauge name
        planned_playback = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK", "op": "=="},
                                                                   sources = {"filter": "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF", "op": "=="})

        assert len(planned_playback) == 9

        # Check production playback completeness
        planned_playback_ = self.query_eboa.get_events(gauge_names = {"filter": "PLANNED_PLAYBACK%", "op": "like"},
                                                                   sources = {"filter": "S2B_OPER_MPL__NPPF__20201001T120000_20201019T150000_0001.EOF", "op": "=="},
                                                                   start_filters = [{"date": "2020-10-15T12:00:00", "op": ">"}],
                                                                   stop_filters = [{"date": "2020-10-15T013:00:00", "op": "<"}])

        assert len(planned_playback_) == 4

        ###
        # Check number of events generated by specific source
        events = self.query_eboa.get_events(sources = {"filter": "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF", "op": "=="})

        assert len(events) == 12

        # Check number of sources generated by specific source
        sources = self.query_eboa.get_sources(names = {"filter": "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF", "op": "=="})

        assert len(sources) == 2

        # Check number of annotations generated by specific source
        annotations = self.query_eboa.get_annotations(sources = {"filter": "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF", "op": "=="})

        assert len(annotations) == 0

        
        # Check numbers of events generated by specific source and gauge name
        satation_schedule = self.query_eboa.get_events(gauge_names = {"filter": "STATION_SCHEDULE", "op": "=="},
                                                                   sources = {"filter": "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF", "op": "=="})

        assert len(satation_schedule) == 6

        # Check satation schedule_
        satation_schedule_ = self.query_eboa.get_events(gauge_names = {"filter": "STATION_SCHEDULE%", "op": "like"},
                                                                   sources = {"filter": "S2B_OPER_MPL_SPSGS__PDMC_20201014T090002_V20201015T090000_20201021T090000.EOF", "op": "=="},
                                                                   start_filters = [{"date": "2020-10-15T09:00:00", "op": ">"}],
                                                                   stop_filters = [{"date": "2020-10-15T013:00:00", "op": "<"}])

        assert len(satation_schedule_) == 6

        ####
        # Check number of events generated by specific source
        events = self.query_eboa.get_events(sources = {"filter": "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF", "op": "=="})

        assert len(events) == 5

        # Check number of sources generated by specific source
        sources = self.query_eboa.get_sources(names = {"filter": "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF", "op": "=="})

        assert len(sources) == 3

        # Check number of annotations generated by specific source
        annotations = self.query_eboa.get_annotations(sources = {"filter": "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF", "op": "=="})

        assert len(annotations) == 1

        
        # Check numbers of events generated by specific source and gauge name
        playback_validity_ = self.query_eboa.get_events(gauge_names = {"filter": "PLAYBACK_VALIDITY%", "op": "like"},
                                                        sources = {"filter": "S2B_OPER_REP_PASS_E_VGS2_20201015T125515_V20201015T124814_20201015T125511.EOF", "op": "=="})

        assert len(playback_validity_) == 2


        # Check LINK_DETAILS annotations
        link_details = self.query_eboa.get_annotations(annotation_cnf_names = {"filter": "LINK_DETAILS_CH1", "op": "=="})

        assert len(link_details) == 1

        assert link_details[0].get_structured_values() == [
            {
                "value": "S2B_20201015123300018854",
                "type": "text",
                "name": "session_id"
            },{
                "value": "18854.0",
                "type": "double",
                "name": "downlink_orbit"
            },
            {
                "value": "S2B",
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

        # Check RAW_ISP_VALIDITY events
        raw_isp_validities = self.query_eboa.get_events(gauge_names = {"filter": "RAW_ISP_VALIDITY", "op": "=="})

        assert len(raw_isp_validities) == 1

        # Check specific RAW_ISP_VALIDITY
        specific_raw_isp_validity1 = self.query_eboa.get_events(gauge_names = {"filter": "RAW_ISP_VALIDITY", "op": "=="},
                                                                start_filters = [{"date": "2020-10-15T11:13:47.897671", "op": "=="}],
                                                                stop_filters = [{"date": "2020-10-15T12:44:30.437086", "op": "=="}])

        assert len(specific_raw_isp_validity1) == 1

        assert specific_raw_isp_validity1[0].get_structured_values() == [
            {
                "name": "status",
                "value": "COMPLETE",
                "type": "text"
            },
            {
                "name": "downlink_orbit",
                "value": "18854.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2B",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "SGS_",
                "type": "text"
            },
            {
                "name": "channel",
                "value": "1.0",
                "type": "double"
            },
            {
                "name": "vcid",
                "value": "4.0",
                "type": "double"
            },
            {
                "name": "playback_type",
                "value": "NOMINAL",
                "type": "text"
            },
            {
                "name": "num_packets",
                "value": "1296000.0",
                "type": "double"
            },
            {
                "name": "num_frames",
                "value": "11528722.0",
                "type": "double"
            },
            {
                "name": "expected_num_packets",
                "value": "0.0",
                "type": "double"
            },
            {
                "name": "diff_expected_received",
                "value": "-1296000.0",
                "type": "double"
            },
            {
                "name": "packet_status",
                "value": "MISSING",
                "type": "text"
            },
            {
                "name": "footprint_details_0",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((-5.078245 26.93806, -5.513987 25.325012, -5.940158 23.710762, -6.357588 22.095406, -6.767043 20.479037, -7.169242 18.861743, -7.564831 17.243609, -7.954437 15.624716, -8.338623 14.005144, -8.717931999999999 12.384971, -9.092873000000001 10.764271, -9.463926000000001 9.143119, -9.831552 7.521586, -10.196191 5.899745, -10.558263 4.277663, -10.918183 2.655411, -11.276346 1.033056, -11.633143 -0.5893350000000001, -11.988965 -2.211696, -12.34418 -3.833962, -12.699186 -5.456068, -13.054346 -7.07795, -13.410062 -8.699543999999999, -13.766717 -10.320788, -14.124711 -11.941619, -14.484469 -13.561974, -14.846392 -15.181793, -15.210959 -16.801012, -15.578598 -18.419571, -15.949831 -20.037408, -16.325161 -21.65446, -16.705139 -23.270664, -17.090379 -24.885958, -17.481473 -26.500277, -17.879162 -28.113555, -18.28414 -29.725725, -18.697262 -31.336715, -19.119401 -32.946454, -19.551532 -34.554864, -19.994776 -36.161865, -20.450269 -37.767369, -20.919435 -39.371283, -21.403706 -40.973506, -21.904831 -42.573925, -22.424702 -44.172416, -22.965482 -45.768843, -23.529711 -47.363045, -24.12014 -48.954852, -24.740177 -50.54405, -25.393538 -52.130411, -26.084753 -53.713654, -26.819035 -55.293453, -27.602551 -56.869426, -28.442765 -58.441101, -29.348382 -60.00793, -30.330286 -61.569218, -31.401411 -63.124133, -32.577962 -64.671621, -33.879954 -66.21036599999999, -35.332534 -67.738694, -36.967877 -69.254425, -38.826946 -70.754751, -40.96362 -72.235879, -43.448241 -73.69275, -46.374736 -75.11836599999999, -49.868533 -76.502971, -54.097206 -77.832716, -59.28155 -79.087633, -65.69788800000001 -80.23902699999999, -73.65479999999999 -81.245997, -83.397205 -82.05363, -94.900795 -82.59644400000001, -107.618988 -82.814238, -120.478859 -82.678003, -132.336728 -82.206211, -142.507262 -81.454308, -150.863771 -80.488356, -157.611633 -79.36650299999999, -163.056298 -78.13277100000001, -167.485748 -76.818442, -171.134013 -75.44525, -174.179971 -74.028233, -176.758262 -72.578014, -178.968873 -71.102086, -180 -70.29794898308189, -180 -63.69129233604828, -179.654045 -64.04431099999999, -178.026514 -65.531254, -176.215172 -67.000469, -174.185206 -68.44843899999999, -171.89365 -69.87069700000001, -169.287345 -71.26151900000001, -166.300327 -72.61345300000001, -162.852001 -73.91685, -158.844715 -75.158987, -154.165293 -76.32330899999999, -148.690869 -77.388334, -142.306715 -78.326949, -134.941398 -79.106538, -126.621002 -79.69098200000001, -117.527697 -80.045974, -108.019193 -80.146636, -98.567553 -79.985353, -89.628311 -79.574237, -81.520506 -78.941079, -74.385775 -78.121309, -68.22217499999999 -77.15048899999999, -62.94369 -76.060121, -58.431531 -74.87591500000001, -54.563925 -73.61814699999999, -51.23101 -72.302393, -48.339299 -70.94056, -45.811577 -69.541766, -43.585305 -68.112978, -41.609679 -66.659628, -39.843967 -65.185912, -38.254979 -63.695167, -36.815829 -62.19003, -35.504523 -60.672617, -34.302886 -59.144654, -33.196019 -57.60753, -32.171317 -56.062412, -31.218404 -54.510247, -30.328386 -52.951842, -29.493786 -51.387868, -28.70822 -49.818896, -27.966155 -48.24542, -27.262921 -46.667852, -26.594344 -45.086563, -25.956912 -43.501863, -25.347467 -41.914034, -24.763272 -40.323317, -24.201916 -38.729932, -23.661221 -37.134072, -23.13932 -35.535912, -22.634463 -33.935611, -22.145158 -32.333313, -21.670013 -30.729149, -21.207789 -29.123244, -20.75737 -27.515711, -20.317714 -25.906656, -19.887911 -24.29618, -19.467082 -22.684377, -19.054459 -21.07134, -18.649307 -19.457152, -18.250953 -17.841899, -17.858777 -16.225662, -17.472184 -14.608516, -17.090634 -12.99054, -16.713604 -11.371806, -16.340607 -9.752388, -15.971177 -8.132356, -15.604866 -6.511781, -15.241246 -4.890733, -14.879906 -3.269278, -14.520436 -1.647486, -14.162452 -0.025421, -13.805558 1.596849, -13.449374 3.219258, -13.093521 4.841742, -12.737607 6.464236, -12.381265 8.086676000000001, -12.02408 9.708996000000001, -11.665676 11.331135, -11.305624 12.953027, -10.943509 14.57461, -10.578893 16.19582, -10.211296 17.816593, -9.840268 19.436866, -9.465255000000001 21.056572, -9.085751 22.675649, -8.701142000000001 24.294028, -8.310815 25.911645, -7.914102 27.528429, -5.078245 26.93806))"
                    }
                ]

            },
            {
                "name": "footprint_details_1",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((180 -70.29794898308189, 179.112651 -69.60593900000001, 177.429305 -68.093594, 175.93733 -66.568073, 174.602703 -65.031689, 173.398962 -63.486204, 172.304772 -61.933033, 171.303404 -60.373259, 170.381015 -58.807779, 169.526445 -57.237304, 168.730452 -55.66242, 167.985278 -54.083616, 167.284585 -52.501286, 166.622787 -50.915779, 165.995391 -49.327373, 165.39836 -47.736318, 164.828321 -46.142824, 164.282338 -44.547072, 163.757795 -42.949227, 163.252529 -41.349427, 162.764468 -39.747803, 162.29196 -38.144465, 161.833406 -36.53952, 161.387446 -34.933061, 160.952855 -33.325177, 160.528485 -31.715951, 160.113387 -30.105458, 159.706583 -28.493775, 159.307302 -26.88097, 158.914748 -25.267113, 158.528232 -23.652268, 158.147117 -22.036501, 157.770772 -20.419876, 157.398677 -18.802453, 157.030259 -17.184297, 156.665062 -15.565468, 156.302592 -13.946027, 155.942407 -12.326037, 155.584083 -10.705559, 155.227187 -9.084656000000001, 154.871339 -7.463388, 154.516121 -5.841819, 154.161167 -4.220013, 153.806084 -2.598032, 153.450493 -0.9759409999999999, 153.094405 0.645953, 152.736606 2.268088, 152.377153 3.890137, 152.015637 5.512031, 151.651661 7.133703, 151.2848 8.755083000000001, 150.914621 10.376101, 150.540667 11.996685, 150.162466 13.616762, 149.77951 15.236257, 149.391277 16.855094, 148.997194 18.473193, 148.596663 20.090474, 148.189035 21.706853, 147.773609 23.322242, 147.349644 24.936551, 146.916303 26.549685, 146.472719 28.161543, 146.017894 29.772018, 145.550771 31.380999, 145.070171 32.988365, 144.574776 34.593983, 144.063171 36.197714, 143.533703 37.799402, 142.984615 39.39888, 142.413849 40.995957, 141.819147 42.590426, 141.197931 44.182054, 140.54725 45.770574, 139.863815 47.355692, 139.143733 48.937059, 138.382663 50.514288, 137.575451 52.086917, 136.716192 53.654417, 135.797954 55.216163, 134.812542 56.771414, 133.750393 58.319298, 132.599931 59.858748, 131.347518 61.3885, 129.976521 62.906987, 128.466901 64.412299, 126.794172 65.90206000000001, 124.928188 67.373284, 122.831958 68.82222400000001, 120.459337 70.24404800000001, 117.753412 71.63258500000001, 114.643472 72.97976300000001, 111.043036 74.275058, 106.848365 75.504656, 101.940172 76.650459, 96.193021 77.68918600000001, 89.496978 78.591571, 81.800461 79.32311199999999, 73.169815 79.846828, 63.844006 80.129634, 54.233799 80.15078800000001, 44.831669 79.908607, 36.069575 79.42120300000001, 28.216092 78.720225, 21.362105 77.842561, 15.470451 76.823387, 10.437216 75.69285499999999, 6.137317 74.47521399999999, 2.449811 73.189285, -0.731962 71.849532, -3.497029 70.466915, -5.918524 69.04986100000001, -8.055403999999999 67.60481, -9.955282 66.13677, -11.656597 64.649658, -13.190349 63.14655, -14.581977 61.629927, -19.808561 62.532722, -18.666035 64.089028, -17.404838 65.6371, -16.001291 67.175347, -14.4258 68.70177, -12.640191 70.213742, -10.595013 71.707793, -8.225567 73.179288, -5.445671 74.621838, -2.140822 76.02664900000001, 1.843025 77.381184, 6.709386 78.667558, 12.719051 79.85990099999999, 20.177036 80.921188, 29.364716 81.800518, 40.369012 82.434184, 52.821304 82.75757, 65.778649 82.729097, 78.050329 82.352744, 88.77579 81.675522, 97.67495 80.76331399999999, 104.882056 79.67821499999999, 110.690355 78.46880899999999, 115.400679 77.170175, 119.264395 75.806659, 122.476786 74.39519199999999, 125.184601 72.94758, 127.497402 71.472193, 129.497494 69.975094, 131.246697 68.46069, 132.79264 66.932322, 134.17173 65.392478, 135.412691 63.843104, 136.538128 62.285705, 137.566072 60.72147, 138.511243 59.151363, 139.385398 57.576141, 140.198483 55.996448, 140.958502 54.412792, 141.672311 52.82561, 142.345626 51.235266, 142.98326 49.642062, 143.589445 48.046268, 144.167634 46.448103, 144.721006 44.847771, 145.252154 43.245438, 145.763449 41.64126, 146.256942 40.035372, 146.734405 38.427895, 147.197507 36.818945, 147.647595 35.208618, 148.086019 33.597014, 148.51387 31.984217, 148.932209 30.370312, 149.341976 28.755377, 149.743998 27.139485, 150.139107 25.522713, 150.527963 23.905125, 150.911279 22.286794, 151.289635 20.667785, 151.663618 19.048162, 152.033769 17.427992, 152.400574 15.807338, 152.764547 14.186264, 153.126104 12.564833, 153.485715 10.943109, 153.843778 9.321154999999999, 154.200708 7.699035, 154.556907 6.076812, 154.912751 4.454549, 155.268644 2.832313, 155.624949 1.210166, 155.981907 -0.41157, 156.340153 -2.033322, 156.699974 -3.654788, 157.061766 -5.275901, 157.425931 -6.896595, 157.79289 -8.516798, 158.163072 -10.136445, 158.536929 -11.755463, 158.914932 -13.373782, 159.297577 -14.991329, 159.685387 -16.608029, 160.078924 -18.223808, 160.47877 -19.838584, 160.885577 -21.45228, 161.300016 -23.064809, 161.722835 -24.676085, 162.154835 -26.286017, 162.596882 -27.894509, 163.049946 -29.501459, 163.515043 -31.106758, 163.993359 -32.710292, 164.486133 -34.311936, 164.994795 -35.911554, 165.520906 -37.509, 166.066204 -39.104112, 166.632683 -40.696709, 167.222496 -42.286596, 167.838196 -43.873546, 168.482564 -45.457309, 169.158853 -47.037599, 169.870744 -48.61409, 170.622457 -50.186407, 171.418941 -51.754111, 172.265794 -53.316705, 173.169744 -54.873586, 174.138506 -56.424058, 175.18131 -57.967285, 176.309059 -59.502267, 177.534743 -61.027802, 178.874107 -62.542411, 180 -63.69129233604828, 180 -70.29794898308189))"
                    }
                ]
            }
        ]
        
        # Check PLAYBACK_VALIDITY_3 events
        playback_validity_3 = self.query_eboa.get_events(gauge_names = {"filter": "PLAYBACK_VALIDITY_3", "op": "=="})

        assert len(playback_validity_3) == 1

        # Check specific PLAYBACK_VALIDITY_3
        playback_validity_3_ = self.query_eboa.get_events(gauge_names = {"filter": "PLAYBACK_VALIDITY_3", "op": "=="},
                                                                start_filters = [{"date": "2020-10-15T12:54:34.898569", "op": "=="}],
                                                                stop_filters = [{"date": "2020-10-15T12:55:11.857864", "op": "=="}])

        assert len(playback_validity_3_) == 1

        assert playback_validity_3_[0].get_structured_values() == [
            {
                "name": "downlink_orbit",
                "value": "18854.0",
                "type": "double"
            },
            {
                "name": "satellite",
                "value": "S2B",
                "type": "text"
            },
            {
                "name": "reception_station",
                "value": "SGS_",
                "type": "text"
            },
            {
                "name": "channel",
                "value": "1.0",
                "type": "double"
            },
            {
                "name": "vcid",
                "value": "3.0",
                "type": "double"
            },
            {
                "name": "playback_type",
                "value": "HKTM",
                "type": "text"
            },
            {
                "name": "status",
                "value": "COMPLETE",
                "type": "text"
            },
            {
                "name": "footprint_details",
                "type": "object",
                "values": [
                    {
                        "name": "footprint",
                        "type": "geometry",
                        "value": "POLYGON ((-30.335023 26.63833, -30.394236 26.420391, -30.453267 26.202428, -30.512119 25.984443, -30.570785 25.766436, -30.629266 25.548405, -30.68758 25.330353, -30.745718 25.112279, -30.803679 24.894183, -30.861466 24.676065, -30.919095 24.457926, -33.696283 25.042707, -33.643501 25.261301, -33.590635 25.479882, -33.537647 25.698447, -33.484533 25.916998, -33.4313 26.135532, -33.377969 26.354053, -33.324507 26.572557, -33.270913 26.791045, -33.217203 27.009518, -33.163378 27.227975, -30.335023 26.63833))"
                    }
                ]

            }
        ]