"""
    Tests
"""
from mock import MagicMock, patch  # create_autospec
import awair_command_line.awair as test

PACKAGE = "awair_command_line.awair."


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


def test_get_aqi_grade():
    """ test
    """
    assert "green" in test.get_aqi_grade(2)
    assert "yellow" in test.get_aqi_grade(51)


def test_get_awair_grade():
    """ test
    """
    tests = {
        100: "Good",
        99: "Good",
        81: "Good",
        80: "Good",
        79: "Fair",
        61: "Fair",
        60: "Fair",
        59: "Poor",
        1: "Poor",
    }

    for score, grade in tests.items():
        assert test.get_awair_grade(score) == grade


def test_augment_data():
    """ test
    """
    config = {"display": "pm25"}
    data = {"score": 85, "temp": 25, "humid": 60, "pm25": 1, "pm10_est": 1}
    result = test.augment_data(config, data)
    assert result["humidity_display"] == "60%"
    assert "77" in result["farenheit_display"]
    assert "4" in result["aqi_display"]


@patch(PACKAGE + "get_awair_config")
@patch(PACKAGE + "delegator.run")
def test_discover_awairs(delegator_run, awair_config, capsys):
    """ test
    """
    awair_config.return_value = True

    tab = "\t"
    nl = "\n"
    ip = "127.0.0.1"
    mac = "aa:aa:aa:aa:aa:aa"

    # One Awair found
    delegator_output = ip + tab + mac
    delegator_run.return_value = MagicMock(return_code=0, out=delegator_output)
    response = test.discover_awairs()
    assert len(response) == 1
    assert response[0] == ip
    reset_mocks(delegator_run, awair_config)

    # Multiple Awairs found
    delegator_output = (ip + tab + mac + nl) * 2
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


def test_error(capsys):
    """ test
    """
    test.error("foobar")
    out, __ = capsys.readouterr()
    assert "ERROR:" in out
    assert "foobar" in out


def test_progress(capsys):
    """ test
    """
    test.progress(True, "foobar")
    out, __ = capsys.readouterr()
    assert "foobar" in out

    test.progress(False, "foobar")
    out, __ = capsys.readouterr()
    assert "foobar" not in out


def test_get_specified_ip():
    """ test
    """
    response = test.get_specified_ip(["--ip", "foobar"])
    assert response == "foobar"

    response = test.get_specified_ip(["--something-else", "blah"])
    assert response is None

    response = test.get_specified_ip([])
    assert response is None


def test_get_specified_mac():
    """ test
    """
    response = test.get_specified_mac(["--mac", "AA-bb"])
    assert response == "aa:bb"

    response = test.get_specified_mac(["--something-else", "blah"])
    assert response is None

    response = test.get_specified_mac([])
    assert response is None
