""" Discovers the Awair devices on the network, and displays their data
"""
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional, Union
import aqi as aqilib
import delegator
import requests


AwairDict = Dict[str, Union[int, float, str]]
NL = "\n"
TAB = "\t"
HTTP_TIMEOUT = 0.5
DISPLAY_KEYS = OrderedDict(
    {
        "aqi": "Purple Air",
        "awair_grade": "Awair grade",
        "pm25": "PM 2.5",
        "pm10_est": "PM 10",
        "farenheit": "Temperature (F)",
        "humidity_formatted": "Humidity",
        "co2": "Carbon Dioxide",
        "voc": "VOC",
        "voc_h2_raw": "VOC Raw",
        "voc_ethanol_raw": "VOC Ethanol",
        "device_uuid": "Device name",
    }
)


def main():
    """ main
    """
    ips = discover_awairs()
    if not ips:
        print()
        print("No Awair devices found on the network. Exiting.")
        return

    for ip in ips:
        config = get_awair_config(ip)
        data = get_awair_data(ip)

        augmented = augment_data(config, data)
        display(augmented)


def augment_data(awair_config: AwairDict, awair_data: AwairDict) -> AwairDict:
    """ Augments the data
    """
    ret = {**awair_config, **awair_data}
    aqi = get_aqi(ret)
    awair_score = int(ret["score"])

    ret["farenheit"] = f"{round(float(ret['temp']) * 1.8 + 32)}º"
    ret["currently_displaying"] = ret[str(ret["display"])]
    ret["aqi"] = f"{aqi}, {get_aqi_grade(aqi)}"
    ret["awair_grade"] = f"{awair_score}, {get_awair_grade(awair_score)}"
    ret["humidity_formatted"] = f"{round(float(ret['humid']))}%"

    return ret


def display(data: AwairDict) -> None:
    """ Prints the data
    """
    print()
    for original_name, new_name in DISPLAY_KEYS.items():
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
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        if not response.ok:
            return None

        return response.json()

    except:  # noqa  # pylint: disable=bare-except
        return None


def discover_awairs() -> List[str]:
    """Tries to discover Awairs via ARP scanning"""

    print("Discovering Awair devices...", end="", flush=True)
    grep = 'grep -v "^Starting\\|^Interface:\\|packets received\\|hosts scanned"'  # noqa pylint: disable=anomalous-backslash-in-string
    exe = f"arp-scan -l --quiet --ignoredups | {grep}"
    response = delegator.run(exe)
    if response.return_code:
        print()
        print("Please install arp-scan")
        print()
        return []

    ret = []
    for line in response.out.split(NL):
        if not line:
            continue

        data = line.split(TAB)
        ip_address = data[0]
        # mac = data[1]

        print(".", end="", flush=True)
        if get_awair_config(ip_address):
            print("+", end="", flush=True)
            ret.append(ip_address)

    print()
    return ret


if __name__ == "__main__":
    main()
