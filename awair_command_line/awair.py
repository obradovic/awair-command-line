""" Discovers the Awair devices on the network, and displays their data
"""
import argparse
from collections import OrderedDict
from datetime import datetime
import sys
from typing import List, Optional
import aqi as aqilib
import delegator
import requests
from awair_command_line.statsd import report_statsd, AwairDict


def main() -> None:
    """ main
    """
    ip_addresses = discover_awairs()
    for ip in ip_addresses:
        config = get_awair_config(ip)
        if not config:
            return

        data = get_awair_data(ip)
        if not data:
            return

        augmented = augment_data(config, data)
        display(augmented)
        report_statsd(augmented)

    if not ip_addresses:
        print("No Awair devices found on the network. Exiting.")


def augment_data(awair_config: AwairDict, awair_data: AwairDict) -> AwairDict:
    """ Augments the data
    """
    ret = {**awair_config, **awair_data}
    aqi = get_aqi(ret)
    awair_score = int(ret["score"])
    farenheit = round(float(ret["temp"]) * 1.8 + 32)

    ret["farenheit"] = farenheit
    ret["farenheit_display"] = f"{farenheit}º"
    ret["number_on_awair"] = ret[str(ret["display"])]
    ret["aqi"] = aqi
    ret["aqi_display"] = f"{aqi}, {get_aqi_grade(aqi)}"
    ret["awair_display"] = f"{awair_score}, {get_awair_grade(awair_score)}"
    ret["humidity_display"] = f"{round(float(ret['humid']))}%"

    return ret


def display(data: AwairDict) -> None:
    """ Prints the data
    """
    display_keys = OrderedDict(
        {
            "aqi_display": "Purple Air",
            "awair_display": "Awair grade",
            "pm25": "PM 2.5",
            "pm10_est": "PM 10",
            "farenheit_display": "Temperature (F)",
            "humidity_display": "Humidity",
            "co2": "Carbon Dioxide",
            "voc": "VOC",
            "voc_h2_raw": "VOC Raw",
            "voc_ethanol_raw": "VOC Ethanol",
            "device_uuid": "Device name",
        }
    )

    print()
    for original_name, new_name in display_keys.items():
        display_name = f"{new_name}:"
        print(f"{display_name:<16} {data[original_name]}")
    print()


def get_aqi(data: AwairDict) -> int:
    """ Returns the AQI for a given PM2.5 numbe
    """
    pm25 = data["pm25"]
    pm10 = data["pm10_est"]

    algorithm = aqilib.ALGO_EPA
    # algorithm = aqilib.ALGO_MEP  # China Ministry of Health

    ret = aqilib.to_aqi(
        [(aqilib.POLLUTANT_PM25, pm25), (aqilib.POLLUTANT_PM10, pm10)], algo=algorithm
    )

    return int(ret)


def get_aqi_grade(score: int) -> str:
    """ Returns the color for the passed-in AQI
        FROM: https://www3.epa.gov/airnow/aqi_brochure_02_14.pdf
    """
    grades_greater_than = {
        -1: "Good (green)",
        50: "Moderate (yellow)",
        100: "Unhealthy for sensitive groups (orange)",
        200: "Unhealthy (red)",
        300: "Very unhealthy (purple)",
        1000: "Hazardous (maroon)",
    }

    ret = ""
    for grade, desc in grades_greater_than.items():
        if score >= grade:
            ret = desc

    return ret


def get_awair_grade(score: int) -> str:
    """ Returns the color for the passed-in AQI
    """
    grades_greater_than = {
        -1: "Poor",
        60: "Fair",
        80: "Good",
    }

    ret = ""
    for grade, desc in grades_greater_than.items():
        if score >= grade:
            ret = desc

    return ret


def get_awair_data(ip_address: str) -> Optional[AwairDict]:
    """ Returns the current Awair data for the passed-in IP
    """
    now = datetime.now().replace(microsecond=0).isoformat()
    url = f"http://{ip_address}/air-data/latest?current_time={now}"
    return get_awair_url(url)


def get_awair_config(ip_address: str) -> Optional[AwairDict]:
    """ Returns the current Awair config for the passed-in IP
    """
    url = f"http://{ip_address}/settings/config/data"
    return get_awair_url(url)


def get_awair_url(url: str) -> Optional[AwairDict]:
    """ Returns JSON from the passed-in URL
    """
    http_timeout = 1.0

    try:
        response = requests.get(url, timeout=http_timeout)
        if not response.ok:
            return None

        return response.json()

    except:  # noqa  # pylint: disable=bare-except
        return None


def discover_awairs() -> List[str]:
    """Tries to discover Awairs via ARP scanning"""
    nl = "\n"
    tab = "\t"

    ip_address = get_specified_ip()
    if ip_address:
        if get_awair_config(ip_address):
            return [ip_address]

        error(f"Awair device not found at {ip_address}")
        return []

    mac = get_specified_mac()
    show_progress = not bool(mac)

    grep = 'grep -v "^Starting\\|^Interface:\\|packets received\\|hosts scanned"'  # noqa pylint: disable=anomalous-backslash-in-string
    exe = f"arp-scan -l --quiet --ignoredups | {grep}"
    progress(show_progress, "Discovering Awair devices...")
    response = delegator.run(exe)
    if response.return_code:
        print()
        print("Please install arp-scan")
        print()
        return []

    ret = []
    for line in response.out.split(nl):
        if not line:
            continue

        data = line.split(tab)
        this_ip = data[0]
        this_mac = data[1]

        if mac:
            if not this_mac == mac:
                continue

        verified = verify_awair(this_ip)
        if verified:
            progress(show_progress, "+")
            ret.append(this_ip)
        else:
            progress(show_progress, ".")

    if mac and (not ret):
        error(f"Awair device not found at {mac}")

    progress(show_progress, nl)
    return ret


def error(string: str) -> None:
    """ Prints an error message
    """
    print(f"ERROR: {string}")


def progress(should_print: bool, string: str) -> None:
    """ Prints and flushes the string, if the first arg is true
    """
    if should_print:
        print(string, end="", flush=True)


def verify_awair(ip_address: str) -> bool:
    """ Verifies an Awair device is at the specified IP
    """
    if get_awair_config(ip_address):
        return True

    return False


def get_specified_ip(the_args: Optional[List[str]] = None) -> Optional[str]:
    """ Returns the IP address, if it was specified on the cmdline
    """
    return get_specified_arg("--ip", the_args)


def get_specified_mac(the_args: Optional[List[str]] = None) -> Optional[str]:
    """ Returns the MAC address, if it was specified on the cmdline
    """
    ret = get_specified_arg("--mac", the_args)
    if ret:
        ret = ret.lower().replace("-", ":")
    return ret


def get_specified_arg(
    arg_name: str, the_args: Optional[List[str]] = None
) -> Optional[str]:
    """ Returns the arg for the passed-in mutually-exclusive list of args
    """
    if not the_args:
        the_args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(arg_name, dest="item")
    parsed, _ = parser.parse_known_args(the_args)
    return parsed.item


if __name__ == "__main__":
    main()
