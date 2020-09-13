""" Discovers the Awair devices on the network, and displays their data
"""
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional, Union
import aqi
import delegator
import requests


AwairDict = Dict[str, Union[int, float, str]]
NL = "\n"
TAB = "\t"
HTTP_TIMEOUT = 0.5
DISPLAY_KEYS = OrderedDict(
    {
        "device_uuid": "Device name",
        "aqi": "Purple Air",
        "currently_displaying": "Current display",
        "pm25": "PM 2.5",
        "pm10_est": "PM 10",
        "farenheit": "Temperature (F)",
        "humidity_formatted": "Humidity",
        "co2": "Carbon Dioxide",
        "voc": "VOC",
        "voc_h2_raw": "VOC Raw",
        "voc_ethanol_raw": "VOC Ethanol",
        "score": "Awair score",
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
    ret["farenheit"] = round(float(ret["temp"]) * 1.8 + 32)
    ret["currently_displaying"] = ret[str(ret["display"])]
    ret["aqi"] = get_aqi(ret)
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

    algorithm = aqi.ALGO_EPA
    # algorithm = aqi.ALGO_MEP  # China Ministry of Health

    ret = aqi.to_aqi(
        [(aqi.POLLUTANT_PM25, pm25), (aqi.POLLUTANT_PM10, pm10)], algo=algorithm
    )

    return int(ret)


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
