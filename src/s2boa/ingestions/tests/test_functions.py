"""
Automated tests for the functions of the ingestion of the S2BOA submodule

Written by DEIMOS Space S.L. (dibb)

module s2boa
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

# Import ingestion
import eboa.ingestion.eboa_ingestion as ingestion

# Import functions
import s2boa.ingestions.functions as s2boa_functions

class TestS2boaFunctions(unittest.TestCase):
    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

    def tearDown(self):
        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()

    def test_associate_footprint_covered_by_one_orbpre_event(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        events = [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T09:50:51.776833",
             "stop": "2018-07-21T09:50:51.776833",
            }

        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")

        assert events_with_footprint == [{
            "gauge": {"insertion_type": "SIMPLE_UPDATE",
                      "name": "GAUGE_NAME",
                      "system": "GAUGE_SYSTEM"},
            "start": "2018-07-21T09:50:51.776833",
            "stop": "2018-07-21T09:50:51.776833",
            "values": [
                {"name": "footprint_details",
                 "type": "object",
                 "values": [{"name": "footprint",
                             "type": "geometry",
                             "value": "-171.455147 -0.281921 -168.925664 0.281908 -168.925664 0.281908 -171.455147 -0.281921"}
                 ]}
            ]}
        ]

    def test_associate_footprint_not_covered_by_orbpre_event(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        events = [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T08:50:51.776833",
             "stop": "2018-07-21T09:50:51.776833",
            }

        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")

        assert events_with_footprint == [{
            "gauge": {"insertion_type": "SIMPLE_UPDATE",
                      "name": "GAUGE_NAME",
                      "system": "GAUGE_SYSTEM"},
            "start": "2018-07-21T08:50:51.776833",
            "stop": "2018-07-21T09:50:51.776833"
            }
        ]

    def test_split_footprint(self):

        filename = "S2A_ORBPRE.EOF"
        file_path = os.path.dirname(os.path.abspath(__file__)) + "/inputs/" + filename

        returned_value = ingestion.command_process_file("s2boa.ingestions.ingestion_orbpre.ingestion_orbpre", file_path, "2018-01-01T00:00:00")

        assert returned_value[0]["status"] == eboa_engine.exit_codes["OK"]["status"]

        events = [
            {"gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "GAUGE_NAME",
                "system": "GAUGE_SYSTEM"
            },
             "start": "2018-07-21T11:10:51.776833",
             "stop": "2018-07-21T12:20:51.776833",
            }

        ]

        events_with_footprint = s2boa_functions.associate_footprints(events, "S2A")

        assert events_with_footprint == [{
            "gauge": {"insertion_type": "SIMPLE_UPDATE",
                      "name": "GAUGE_NAME",
                      "system": "GAUGE_SYSTEM"},
            "start": "2018-07-21T11:10:51.776833",
            "stop": "2018-07-21T12:20:51.776833",
            "values": [
                {"name": "footprint_details_0",
                 "type": "object",
                 "values": [{"name": "footprint",
                             "type": "geometry",
                             "value": "-166.737509 -72.55179 "
                             "-168.466494 -71.414361 "
                             "-170.013452 -70.264317 "
                             "-171.406998 -69.103694 "
                             "-172.670281 -67.934107 "
                             "-173.82217 -66.756851 "
                             "-174.878239 -65.572981 "
                             "-175.851389 -64.383362 "
                             "-176.752404 -63.18871 "
                             "-177.590364 -61.989623 "
                             "-178.372826 -60.78659 "
                             "-179.106276 -59.580029 "
                             "-179.796258 -58.370297 -180.0 "
                             "-57.990952831103854 -180.0 "
                             "-48.7409196773976 -179.826356 "
                             "-49.116341 -179.239659 "
                             "-50.329076 -178.626072 "
                             "-51.539043 -177.98297 "
                             "-52.746007 -177.307427 "
                             "-53.949709 -176.596134 "
                             "-55.14985 -175.84535 "
                             "-56.346092 -175.050855 "
                             "-57.538055 -174.207744 "
                             "-58.725288 -173.310447 "
                             "-59.907278 -172.352561 "
                             "-61.08343 -171.326699 "
                             "-62.25305 -170.224353 "
                             "-63.415333 -169.035544 "
                             "-64.569318 -167.748648 "
                             "-65.713872 -166.350073 "
                             "-66.847648 -164.823852 "
                             "-67.969036 -163.151221 "
                             "-69.076102 -161.310017 "
                             "-70.166504 -159.274035 "
                             "-71.237382 -166.737509 "
                             "-72.55179"}]},
                {"name": "footprint_details_1",
                 "type": "object",
                 "values": [{"name": "footprint",
                             "type": "geometry",
                             "value": "180.0 -57.990952831103854 "
                             "179.552466 -57.157696 "
                             "178.935714 -55.942492 "
                             "178.349985 -54.724905 "
                             "177.79217 -53.505127 "
                             "177.259546 -52.28333 "
                             "176.749715 -51.059663 "
                             "176.260526 -49.834258 "
                             "175.790121 -48.60723 "
                             "175.336856 -47.378682 "
                             "174.899244 -46.148706 "
                             "174.475952 -44.917385 "
                             "174.065768 -43.684794 "
                             "173.667596 -42.451003 "
                             "173.280496 -41.216071 "
                             "172.903585 -39.980057 "
                             "172.536059 -38.743011 "
                             "172.177184 -37.504985 "
                             "171.826254 -36.266023 "
                             "171.482694 -35.026168 "
                             "171.14594 -33.785461 "
                             "170.815473 -32.543938 "
                             "170.490812 -31.301637 "
                             "170.17149 -30.058593 "
                             "169.857107 -28.814839 "
                             "169.547287 -27.570409 "
                             "169.241673 -26.325332 "
                             "168.939926 -25.079642 "
                             "168.64172 -23.833366 "
                             "168.346753 -22.586536 "
                             "168.054761 -21.339181 "
                             "167.765477 -20.091329 "
                             "167.478647 -18.843009 "
                             "167.194031 -17.594249 "
                             "166.911379 -16.345079 "
                             "166.630491 -15.095526 "
                             "166.351156 -13.845619 "
                             "166.073167 -12.595385 "
                             "165.796327 -11.344855 "
                             "165.52043 -10.094054 "
                             "165.245298 -8.843014 "
                             "164.970749 -7.591761 "
                             "164.696603 -6.340325 "
                             "164.422682 -5.088735 "
                             "164.148803 -3.83702 163.874791 "
                             "-2.585209 163.600477 -1.333333 "
                             "163.326229 -0.08443 163.050772 "
                             "1.167514 162.774482 2.419434 "
                             "162.497179 3.671298 162.218683 "
                             "4.923075 161.93881 6.174736 "
                             "161.657368 7.426246 161.374162 "
                             "8.677576 161.088992 9.928692 "
                             "160.801651 11.17956 160.511924 "
                             "12.430149 160.219588 13.680424 "
                             "159.92441 14.93035 159.626149 "
                             "16.179892 159.324552 17.429015 "
                             "159.019348 18.677681 "
                             "158.710255 19.925853 "
                             "158.396975 21.173493 "
                             "158.079196 22.42056 157.756589 "
                             "23.667013 157.428791 24.912811 "
                             "157.095423 26.157909 "
                             "156.756079 27.402261 "
                             "156.410326 28.645819 "
                             "156.057713 29.888535 "
                             "155.697727 31.130354 "
                             "155.329827 32.371222 "
                             "154.953431 33.611079 "
                             "154.567908 34.849863 "
                             "154.172586 36.087509 "
                             "153.766719 37.323945 "
                             "153.349487 38.559093 "
                             "152.920006 39.792872 "
                             "152.477305 41.025192 "
                             "152.020331 42.255955 "
                             "151.547925 43.485058 "
                             "151.058781 44.712381 "
                             "150.551472 45.937797 "
                             "150.024419 47.161164 "
                             "149.475866 48.382325 "
                             "148.903895 49.601109 "
                             "148.306283 50.817317 "
                             "147.680581 52.03073 147.024032 "
                             "53.241101 146.333529 54.448149 "
                             "145.605586 55.651562 "
                             "144.836194 56.850974 "
                             "144.020787 58.045969 "
                             "143.154158 59.236067 "
                             "142.230331 60.420717 "
                             "141.242443 61.599277 "
                             "140.182544 62.770999 "
                             "139.041351 63.934995 "
                             "137.808082 65.090225 "
                             "136.470125 66.235453 "
                             "135.012683 67.369203 "
                             "133.418398 68.489716 "
                             "131.666641 69.594844 "
                             "129.733123 70.68199 127.589164 "
                             "71.747986 125.200997 72.788946 "
                             "122.52919 73.800103 119.528035 "
                             "74.775551 116.145804 75.708014 "
                             "112.325959 76.588564 "
                             "108.010264 77.406349 "
                             "103.145039 78.148418 97.691525 "
                             "78.799747 91.640987 79.343698 "
                             "85.032746 79.763164 77.969095 "
                             "80.042419 70.618118 80.169524 "
                             "63.196508 80.138626 55.933778 "
                             "79.95115 49.031103 79.615566 "
                             "42.631763 79.14559 36.812279 "
                             "78.557751 31.591062 77.869172 "
                             "26.945707 77.095927 22.830088 "
                             "76.25226 19.187735 75.350303 "
                             "15.960532 74.40013 13.09353 "
                             "73.409997 10.537318 72.386607 "
                             "8.248707 71.335383 6.190494 "
                             "70.260734 4.330976 69.166248 "
                             "2.643252 68.054857 1.104519 "
                             "66.928973 -0.304432 65.790571 "
                             "-1.599948 64.641298 -2.795933 "
                             "63.482531 -3.904244 62.315426 "
                             "-4.935087 61.140964 -5.897131 "
                             "59.959968 -6.797894 58.773142 "
                             "-7.643888 57.581093 -8.440776 "
                             "56.384344 -9.193522 55.183351 "
                             "-9.906441 53.978505 -10.583311 "
                             "52.770149 -11.227484 51.558585 "
                             "-11.841924 50.344079 "
                             "-12.429273 49.126869 -12.99189 "
                             "47.907164 -13.53184 46.68515 "
                             "-14.050996 45.460994 "
                             "-14.551043 44.234847 -15.0335 "
                             "43.006844 -15.499763 41.777112 "
                             "-15.951044 40.54576 -16.38847 "
                             "39.312892 -16.813065 38.0786 "
                             "-17.225765 36.842972 -17.62744 "
                             "35.606089 -18.018865 34.368025 "
                             "-18.400751 33.128848 "
                             "-18.773763 31.888624 "
                             "-19.138511 30.647413 "
                             "-19.495566 29.405273 "
                             "-19.845457 28.162259 "
                             "-20.188658 26.918421 "
                             "-20.525623 25.673809 "
                             "-20.856774 24.42847 -21.182506 "
                             "23.182448 -21.503199 21.935788 "
                             "-21.819187 20.688531 "
                             "-22.130799 19.440717 "
                             "-22.438343 18.192386 -22.74211 "
                             "16.943576 -23.04238 15.694325 "
                             "-23.339412 14.444667 "
                             "-23.633455 13.19464 -23.924748 "
                             "11.944279 -24.21352 10.693616 "
                             "-24.499992 9.442686 -24.784373 "
                             "8.191523 -25.066869 6.940159 "
                             "-25.347678 5.688626 -25.626994 "
                             "4.436956 -25.905004 3.185181 "
                             "-28.438059 3.749172 -28.163532 "
                             "5.001156 -27.888951 6.253142 "
                             "-27.614136 7.5051 -27.338909 "
                             "8.757001 -27.063086 10.008816 "
                             "-26.786493 11.260517 "
                             "-26.508939 12.512073 "
                             "-26.230222 13.763455 "
                             "-25.950144 15.014635 "
                             "-25.668498 16.265583 "
                             "-25.385076 17.516269 "
                             "-25.099665 18.766666 -24.81202 "
                             "20.016742 -24.521898 21.266469 "
                             "-24.229044 22.515816 "
                             "-23.933189 23.764752 "
                             "-23.634076 25.01325 -23.331382 "
                             "26.261275 -23.024786 27.508797 "
                             "-22.713949 28.755783 "
                             "-22.398508 30.002199 "
                             "-22.078096 31.248012 "
                             "-21.752286 32.493186 "
                             "-21.420618 33.737685 "
                             "-21.082606 34.981468 "
                             "-20.737724 36.224496 "
                             "-20.385416 37.466727 "
                             "-20.025075 38.708116 "
                             "-19.655998 39.948615 "
                             "-19.277444 41.188171 "
                             "-18.888598 42.426729 "
                             "-18.488567 43.664229 -18.07641 "
                             "44.90061 -17.650988 46.135797 "
                             "-17.211088 47.369712 "
                             "-16.755358 48.602267 "
                             "-16.282287 49.833367 "
                             "-15.790228 51.062907 "
                             "-15.277251 52.290765 "
                             "-14.741191 53.516804 "
                             "-14.179611 54.740869 "
                             "-13.589737 55.962785 "
                             "-12.968433 57.182351 "
                             "-12.312077 58.399339 "
                             "-11.616436 59.613475 -10.87665 "
                             "60.824446 -10.087059 62.031885 "
                             "-9.241047 63.23536 -8.330889 "
                             "64.434368 -7.347258 65.628286 "
                             "-6.279132 66.816378 -5.113281 "
                             "67.99775 -3.833723 69.17131 "
                             "-2.421113 70.335722 -0.85156 "
                             "71.489305 0.904351 72.62995 "
                             "2.883114 73.754987 5.130284 "
                             "74.860987 7.702846 75.943525 "
                             "10.672272 76.996792 14.127714 "
                             "78.01311 18.178399 78.982303 "
                             "22.953791 79.890858 28.597033 "
                             "80.720998 35.244539 81.449925 "
                             "42.982828 82.04975 51.778116 "
                             "82.489511 61.402091 82.740082 "
                             "71.413122 82.781747 81.25036 "
                             "82.611011 90.408092 82.241848 "
                             "98.571594 81.70067 105.638726 "
                             "81.018496 111.658487 80.224771 "
                             "116.754687 79.344379 "
                             "121.071391 78.396992 "
                             "124.744657 77.39766 127.891832 "
                             "76.357752 130.609609 75.285827 "
                             "132.975996 74.188356 "
                             "135.053381 73.070274 "
                             "136.891362 71.935348 "
                             "138.529703 70.786518 "
                             "140.000361 69.626092 "
                             "141.329172 68.455899 "
                             "142.537267 67.277415 "
                             "143.641779 66.091811 144.65693 "
                             "64.900053 145.594543 63.702933 "
                             "146.464513 62.501111 "
                             "147.275225 61.29514 148.03371 "
                             "60.08548 148.745948 58.872518 "
                             "149.417091 57.656586 "
                             "150.051577 56.437971 "
                             "150.653271 55.21692 151.225537 "
                             "53.993647 151.771245 52.768334 "
                             "152.292956 51.541143 "
                             "152.792926 50.312217 "
                             "153.273151 49.081682 "
                             "153.735458 47.849655 "
                             "154.181366 46.616232 "
                             "154.612286 45.381503 "
                             "155.029483 44.145549 "
                             "155.434095 42.908446 "
                             "155.827181 41.670261 "
                             "156.209652 40.431056 "
                             "156.582337 39.190887 "
                             "156.946005 37.949807 "
                             "157.301356 36.707865 "
                             "157.649048 35.465108 "
                             "157.989678 34.221581 "
                             "158.323764 32.977322 "
                             "158.651807 31.732372 "
                             "158.974269 30.486768 "
                             "159.291583 29.240546 "
                             "159.604175 27.993742 "
                             "159.912387 26.746389 "
                             "160.216567 25.49852 160.517043 "
                             "24.250165 160.814121 23.001358 "
                             "161.10811 21.752129 161.39927 "
                             "20.502509 161.687855 19.252527 "
                             "161.974112 18.002213 "
                             "162.258277 16.751597 "
                             "162.540585 15.500708 "
                             "162.821253 14.249577 163.10048 "
                             "12.998231 163.378468 11.7467 "
                             "163.655413 10.495012 "
                             "163.931508 9.243198 164.206949 "
                             "7.991288 164.481908 6.739309 "
                             "164.756563 5.487291 165.031093 "
                             "4.235263 165.305675 2.983256 "
                             "165.580491 1.7313 165.855711 "
                             "0.479424 166.13132 -0.769242 "
                             "166.407858 -2.020842 "
                             "166.685331 -3.272271 "
                             "166.963923 -4.523499 "
                             "167.243816 -5.774493 "
                             "167.525197 -7.025224 167.80826 "
                             "-8.27566 168.093204 -9.52577 "
                             "168.380234 -10.775521 "
                             "168.669559 -12.024879 168.9614 "
                             "-13.273813 169.255986 "
                             "-14.522289 169.553556 "
                             "-15.770273 169.854359 "
                             "-17.017731 170.158653 "
                             "-18.264626 170.466716 "
                             "-19.510922 170.778841 "
                             "-20.756583 171.095335 "
                             "-22.001571 171.416523 "
                             "-23.245846 171.742746 "
                             "-24.489368 172.074374 "
                             "-25.732094 172.411803 "
                             "-26.973981 172.755455 "
                             "-28.214984 173.10578 "
                             "-29.455056 173.463259 "
                             "-30.694145 173.828405 -31.9322 "
                             "174.201791 -33.169165 "
                             "174.584027 -34.40498 "
                             "174.975771 -35.639584 "
                             "175.377738 -36.872909 "
                             "175.790685 -38.104882 "
                             "176.215482 -39.335425 "
                             "176.653059 -40.564455 "
                             "177.104432 -41.791878 "
                             "177.570721 -43.017596 "
                             "178.053133 -44.241498 "
                             "178.553038 -45.463465 "
                             "179.071948 -46.683363 "
                             "179.611531 -47.901043 180.0 "
                             "-48.7409196773976 180.0 "
                             "-57.990952831103854"}]}]}]
