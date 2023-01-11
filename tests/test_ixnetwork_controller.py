"""
Test IxNetworkController2GDriver.
"""
# pylint: disable=redefined-outer-name
import json
import time
from pathlib import Path
from typing import Iterable

import pytest
from _pytest.fixtures import SubRequest
from cloudshell.api.cloudshell_api import AttributeNameValue, CloudShellAPISession, InputNameValue
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.traffic.helpers import get_reservation_id, get_resources_from_reservation, set_family_attribute
from cloudshell.traffic.tg import IXIA_CHASSIS_MODEL, IXNETWORK_CONTROLLER_MODEL
from shellfoundry_traffic.test_helpers import TestHelpers, create_session_from_config
from trafficgenerator.tgn_utils import TgnError

from src.ixn_driver import IxNetworkController2GDriver

ALIAS = "IXN Controller"

LINUX_910 = "192.168.65.23:443"
WINDOWS_910 = "localhost:11009"
PORTS_910 = ["IxVM 9.10 - 1 - offline-debug/Module1/Port1", "IxVM 9.10 - 1 - offline-debug/Module1/Port2"]

server_properties = {
    "linux_910": {"server": LINUX_910, "ports": PORTS_910, "auth": ("admin", "admin"), "config_version": "ngpf"},
    "windows_910": {"server": WINDOWS_910, "ports": PORTS_910, "auth": None, "config_version": "classic"},
    "windows_910_ngpf": {"server": WINDOWS_910, "ports": PORTS_910, "auth": None, "config_version": "ngpf"},
}

LICENSE_SERVER = "172.30.150.53"


@pytest.fixture(scope="session")
def session() -> CloudShellAPISession:
    """Yield session."""
    return create_session_from_config()


@pytest.fixture()
def test_helpers(session: CloudShellAPISession) -> Iterable[TestHelpers]:
    """Yield initialized TestHelpers object."""
    test_helpers = TestHelpers(session)
    test_helpers.create_reservation()
    yield test_helpers
    test_helpers.end_reservation()


@pytest.fixture(params=["windows_910_ngpf"])
def server(request: SubRequest) -> list:
    """Yield server information."""
    controller: str = server_properties[request.param]["server"]  # type: ignore
    controller_address, controller_port = controller.split(":")
    ports = server_properties[request.param]["ports"]
    config_version = server_properties[request.param]["config_version"]
    return [controller_address, controller_port, ports, config_version]


@pytest.fixture()
def driver(test_helpers: TestHelpers, server: list) -> Iterable[IxNetworkController2GDriver]:
    """Yield initialized IxNetworkController2GDriver."""
    controller_address, controller_port, _, _ = server
    attributes = {
        f"{IXNETWORK_CONTROLLER_MODEL}.Address": controller_address,
        f"{IXNETWORK_CONTROLLER_MODEL}.Controller TCP Port": controller_port,
        f"{IXNETWORK_CONTROLLER_MODEL}.User": "admin",
        f"{IXNETWORK_CONTROLLER_MODEL}.Password": "DxTbqlSgAVPmrDLlHvJrsA==",
        f"{IXNETWORK_CONTROLLER_MODEL}.License Server": LICENSE_SERVER,
    }
    init_context = test_helpers.service_init_command_context(IXNETWORK_CONTROLLER_MODEL, attributes)
    driver = IxNetworkController2GDriver()
    driver.initialize(init_context)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session: CloudShellAPISession, test_helpers: TestHelpers, server: list) -> ResourceCommandContext:
    """Yield ResourceCommandContext for shell command testing."""
    controller_address, controller_port, ports, _ = server
    attributes = [
        AttributeNameValue(f"{IXNETWORK_CONTROLLER_MODEL}.Address", controller_address),
        AttributeNameValue(f"{IXNETWORK_CONTROLLER_MODEL}.Controller TCP Port", controller_port),
        AttributeNameValue(f"{IXNETWORK_CONTROLLER_MODEL}.User", "admin"),
        AttributeNameValue(f"{IXNETWORK_CONTROLLER_MODEL}.Password", "admin"),
        AttributeNameValue(f"{IXNETWORK_CONTROLLER_MODEL}.License Server", LICENSE_SERVER),
    ]
    session.AddServiceToReservation(test_helpers.reservation_id, IXNETWORK_CONTROLLER_MODEL, ALIAS, attributes)
    context = test_helpers.resource_command_context(service_name=ALIAS)
    session.AddResourcesToReservation(test_helpers.reservation_id, ports)
    reservation_ports = get_resources_from_reservation(context, f"{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort")
    set_family_attribute(context, reservation_ports[0].Name, "Logical Name", "Port 1")
    set_family_attribute(context, reservation_ports[1].Name, "Logical Name", "Port 2")
    return context


class TestIxNetworkControllerDriver:
    """Test direct driver calls."""

    def test_hidden_commands(self, driver: IxNetworkController2GDriver, context: ResourceCommandContext) -> None:
        """Test hidden commands - get_session_id, get_children etc."""
        session_id = driver.get_session_id(context)
        root_obj = f"{session_id}ixnetwork"
        ixn_globals = driver.get_children(context, obj_ref=root_obj, child_type="globals")
        globals_obj = ixn_globals[0]
        preferences = driver.get_children(context, obj_ref=globals_obj, child_type="preferences")
        preferences_obj = preferences[0]
        driver.set_attribute(context, obj_ref=preferences_obj, attr_name="connectPortsOnLoadConfig", attr_value="False")
        preferences_attrs = driver.get_attributes(context, obj_ref=preferences_obj)
        assert preferences_attrs["connectPortsOnLoadConfig"] is False
        driver.set_attribute(context, obj_ref=preferences_obj, attr_name="connectPortsOnLoadConfig", attr_value="True")
        preferences_attrs = driver.get_attributes(context, obj_ref=preferences_obj)
        assert preferences_attrs["connectPortsOnLoadConfig"] is True

    def test_load_config(self, driver: IxNetworkController2GDriver, context: ResourceCommandContext, server: list) -> None:
        """Test load configuration command."""
        self._load_config(driver, context, server, "test_config")

    def test_run_traffic(self, driver: IxNetworkController2GDriver, context: ResourceCommandContext, server: list) -> None:
        """Test complete cycle - from load_config to get_statistics."""
        self._load_config(driver, context, server, "test_config")
        driver.send_arp(context)
        driver.start_protocols(context)
        time.sleep(8)
        driver.stop_traffic(context)
        driver.start_traffic(context, "False")
        driver.stop_traffic(context)
        stats = driver.get_statistics(context, "Port Statistics", "JSON", "")
        assert int(stats["Port 1"]["Frames Tx."]) >= 200
        assert int(stats["Port 1"]["Frames Tx."]) <= 1800
        driver.start_traffic(context, "True")
        time.sleep(4)
        stats = driver.get_statistics(context, "Port Statistics", "JSON", "")
        assert int(stats["Port 1"]["Frames Tx."]) >= 2000
        driver.get_statistics(context, "Port Statistics", "csv", "")
        driver.stop_protocols(context)

    def test_run_quick_test(self, driver: IxNetworkController2GDriver, context: ResourceCommandContext, server: list) -> None:
        """Test run_quick_test command."""
        self._load_config(driver, context, server, "quick_test")
        driver.run_quick_test(context, "QuickTest1")

    def test_negative(self, driver: IxNetworkController2GDriver, context: ResourceCommandContext, server: list) -> None:
        """Negative tests."""
        reservation_ports = get_resources_from_reservation(context, f"{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort")
        assert len(reservation_ports) == 2
        config_file_name = Path(__file__).parent.joinpath(f"test_config_{server[3]}.ixncfg").as_posix()
        set_family_attribute(context, reservation_ports[0].Name, "Logical Name", "Port 1")
        set_family_attribute(context, reservation_ports[1].Name, "Logical Name", "")
        with pytest.raises(TgnError):
            driver.load_config(context, config_file_name)
        set_family_attribute(context, reservation_ports[1].Name, "Logical Name", "Port 1")
        with pytest.raises(TgnError):
            driver.load_config(context, config_file_name)
        set_family_attribute(context, reservation_ports[1].Name, "Logical Name", "Port x")
        with pytest.raises(TgnError):
            driver.load_config(context, config_file_name)
        # cleanup
        set_family_attribute(context, reservation_ports[1].Name, "Logical Name", "Port 2")

    @staticmethod
    def _load_config(
        driver: IxNetworkController2GDriver, context: ResourceCommandContext, server: list, config_name: str
    ) -> None:
        """Get full path to the requested configuration file based on fixture and run load_config."""
        config_file = Path(__file__).parent.joinpath(f"{config_name}_{server[3]}.ixncfg")
        driver.load_config(context, config_file.as_posix())


class TestIxNetworkControllerShell:
    """Test indirect Shell calls."""

    def test_hidden_commands(self, session: CloudShellAPISession, context: ResourceCommandContext) -> None:
        """Test hidden commands - get_session_id, get_children etc."""
        session_id = session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_session_id")
        root_obj = f"/{session_id.Output[1:-1]}/ixnetwork"
        cmd_inputs = [InputNameValue("obj_ref", root_obj), InputNameValue("child_type", "globals")]
        ixn_globals = session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_children", cmd_inputs)
        globals_obj = json.loads(ixn_globals.Output)[0]
        cmd_inputs = [InputNameValue("obj_ref", globals_obj), InputNameValue("child_type", "preferences")]
        preferences = session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_children", cmd_inputs)
        preferences_obj = json.loads(preferences.Output)[0]
        cmd_inputs = [InputNameValue("obj_ref", preferences_obj)]
        preferences_attrs = session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_attributes", cmd_inputs)
        assert json.loads(preferences_attrs.Output)["connectPortsOnLoadConfig"] is False
        cmd_inputs = [
            InputNameValue("obj_ref", preferences_obj),
            InputNameValue("attr_name", "connectPortsOnLoadConfig"),
            InputNameValue("attr_value", "True"),
        ]
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "set_attribute", cmd_inputs)
        cmd_inputs = [InputNameValue("obj_ref", preferences_obj)]
        preferences_attrs = session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_attributes", cmd_inputs)
        assert json.loads(preferences_attrs.Output)["connectPortsOnLoadConfig"] is True

    def test_load_config(self, session: CloudShellAPISession, context: ResourceCommandContext, server: list) -> None:
        """Test load configuration command."""
        self._load_config(session, context, ALIAS, server, "test_config")

    def test_run_traffic(self, session: CloudShellAPISession, context: ResourceCommandContext, server: list) -> None:
        """Test complete cycle - from load_config to get_statistics."""
        self._load_config(session, context, ALIAS, server, "test_config")
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "send_arp")
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "start_protocols")
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "stop_traffic")
        cmd_inputs = [InputNameValue("blocking", "True")]
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "start_traffic", cmd_inputs)
        cmd_inputs = [InputNameValue("view_name", "Port Statistics"), InputNameValue("output_type", "JSON")]
        stats = session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_statistics", cmd_inputs)
        assert int(json.loads(stats.Output)["Port 1"]["Frames Tx."]) >= 2000

    def test_run_quick_test(self, session: CloudShellAPISession, context: ResourceCommandContext, server: list) -> None:
        """Test run_quick_test command."""
        self._load_config(session, context, ALIAS, server, "quick_test")
        cmd_inputs = [InputNameValue("test", "QuickTest1")]
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "run_quick_test", cmd_inputs)

    # pylint: disable=too-many-arguments
    @staticmethod
    def _load_config(
        session: CloudShellAPISession, context: ResourceCommandContext, alias: str, server: list, config_name: str
    ) -> None:
        """Get full path to the requested configuration file based on fixture and run load_config."""
        config_file = Path(__file__).parent.joinpath(f"{config_name}_{server[3]}.ixncfg")
        cmd_inputs = [InputNameValue("config_file_location", config_file.as_posix())]
        session.ExecuteCommand(get_reservation_id(context), alias, "Service", "load_config", cmd_inputs)
