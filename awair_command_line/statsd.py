""" Statsd reporting
"""
import argparse
import sys
from typing import Dict, List, Optional, Union
from datadog import initialize, statsd

AwairDict = Dict[str, Union[int, float, str]]
initialize()


def report_statsd(data: AwairDict) -> None:
    """ Reports to statsd
    """
    if not get_statsd_reporting():
        return

    display_keys = {
        "aqi": "purple_air",
        "co2": "co2",
        "dew_point": "dew_point",
        "farenheit": "temperature",
        "humid": "humidity",
        "pm10_est": "pm10",
        "pm25": "pm25",
        "score": "awair_score",
        "voc": "voc",
        "voc_h2_raw": "voc_raw",
        "voc_baseline": "voc_baseline",
        "voc_ethanol_raw": "voc_ethanol",
    }

    device_name = str(data["device_uuid"]).replace("awair-", "")
    tags = [f"device:{device_name}"]

    for original_name, new_name in display_keys.items():
        statsd_key = f"awair.{new_name}"
        number = int(data[original_name])

        statsd.gauge(statsd_key, number, tags)


def get_statsd_reporting(the_args: Optional[List[str]] = None) -> bool:
    """ Returns whether we should do statsd reporting or not
    """
    if not the_args:
        the_args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("--statsd", dest="item", action="store_true")
    parsed, _ = parser.parse_known_args(the_args)
    return bool(parsed.item)
