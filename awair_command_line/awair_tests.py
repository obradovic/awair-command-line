"""
    Tests
"""
from mock import MagicMock, patch  # create_autospec
import awair.awair as test


def reset_mocks(*mocks) -> None:
    """ Resets all the mocks
    """
    for mock in mocks:
        mock.reset_mock()


def test_get_aqi():
    """ test
    """
    result = test.get_aqi({"pm25": 10, "pm10_est": 10})
    assert result == 42  # the answer to life, the universe, and everything

    result = test.get_aqi({"pm25": 100, "pm10_est": 100})
    assert result == 174


def test_augment_data():
    """ test
    """
    config = {"display": "pm25"}
    data = {"temp": 25, "humid": 60, "pm25": 1, "pm10_est": 1}
    result = test.augment_data(config, data)
    assert result["humidity_formatted"] == "60%"
    assert result["farenheit"] == 77
    assert result["aqi"] == 4


@patch("awair.awair.get_awair_config")
@patch("awair.awair.delegator.run")
def test_discover_awairs(delegator_run, awair_config, capsys):
    """ test
    """
    awair_config.return_value = True

    ip = "127.0.0.1"
    mac = "aa:aa:aa:aa:aa:aa"

    # One Awair found
    delegator_output = ip + test.TAB + mac
    delegator_run.return_value = MagicMock(return_code=0, out=delegator_output)
    response = test.discover_awairs()
    assert len(response) == 1
    assert response[0] == ip
    reset_mocks(delegator_run, awair_config)

    # Multiple Awairs found
    delegator_output = (ip + test.TAB + mac + test.NL) * 2
    delegator_run.return_value = MagicMock(return_code=0, out=delegator_output)
    response = test.discover_awairs()
    assert len(response) == 2
    assert response[0] == ip
    assert response[1] == ip
    reset_mocks(delegator_run, awair_config)

    # No Awairs found
    delegator_output = ""
    delegator_run.return_value = MagicMock(return_code=0, out=delegator_output)
    response = test.discover_awairs()
    assert response == []
    reset_mocks(delegator_run, awair_config)

    # arp-scan not installed
    delegator_run.return_value = MagicMock(return_code=1)
    response = test.discover_awairs()
    assert response == []
    out, __ = capsys.readouterr()
    assert "Please" in out
    reset_mocks(delegator_run, awair_config)
