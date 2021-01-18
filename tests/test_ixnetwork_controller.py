"""
Test IxNetworkController2GDriver.
"""
import json
import time
from os import path

import pytest

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue, CloudShellAPISession
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.traffic.helpers import set_family_attribute, get_reservation_id, get_resources_from_reservation
from cloudshell.traffic.tg import IXNETWORK_CONTROLLER_MODEL, IXIA_CHASSIS_MODEL, PERFECT_STORM_CHASSIS_MODEL
from shellfoundry_traffic.test_helpers import create_session_from_config, TestHelpers

from src.ixn_driver import IxNetworkController2GDriver


ALIAS = 'IXN Controller'

chassis_900 = '192.168.65.37'
chassis_910 = '192.168.65.21'

linux_900 = '192.168.65.34:443'
linux_910 = '192.168.65.23:443'

windows_900 = 'localhost:11009'
windows_910 = 'localhost:11009'

ports_900 = ['ixia-900-1/Module1/Port2', 'ixia-900-1/Module1/Port1']
ports_910 = ['ixia-910-1/Module1/Port2', 'ixia-910-1/Module1/Port1']


server_properties = {'linux_900': {'server': linux_900, 'ports': ports_900, 'auth': ('admin', 'admin'),
                                   'config_version': 'ngpf'},
                     'linux_910': {'server': linux_910, 'ports': ports_910, 'auth': ('admin', 'admin'),
                                   'config_version': 'ngpf'},
                     'windows_900': {'server': windows_900, 'ports': ports_900, 'auth': None,
                                     'config_version': 'classic'},
                     'windows_900_ngpf': {'server': windows_900, 'ports': ports_900, 'auth': None,
                                          'config_version': 'ngpf'},
                     'windows_910': {'server': windows_910, 'ports': ports_910, 'auth': None,
                                     'config_version': 'classic'},
                     'windows_910_ngpf': {'server': windows_910, 'ports': ports_910, 'auth': None,
                                          'config_version': 'ngpf'}}


@pytest.fixture(scope='session')
def session() -> CloudShellAPISession:
    yield create_session_from_config()


@pytest.fixture()
def test_helpers(session: CloudShellAPISession) -> TestHelpers:
    test_helpers = TestHelpers(session)
    test_helpers.create_reservation()
    yield test_helpers
    test_helpers.end_reservation()


@pytest.fixture(params=['linux_910'])
def server(request) -> list:
    controller_address = server_properties[request.param]['server'].split(':')[0]
    controller_port = server_properties[request.param]['server'].split(':')[1]
    config_version = server_properties[request.param]['config_version']
    ports = server_properties[request.param]['ports']
    yield controller_address, controller_port, config_version, ports


@pytest.fixture()
def session() -> CloudShellAPISession:
    yield create_session_from_config()


@pytest.fixture()
def test_helpers(session: CloudShellAPISession) -> TestHelpers:
    test_helpers = TestHelpers(session)
    test_helpers.create_reservation()
    yield test_helpers
    test_helpers.end_reservation()


@pytest.fixture()
def driver(test_helpers: TestHelpers, server: list) -> IxNetworkController2GDriver:
    controller_address, controller_port, _, _ = server
    attributes = {f'{IXNETWORK_CONTROLLER_MODEL}.Address': controller_address,
                  f'{IXNETWORK_CONTROLLER_MODEL}.Controller TCP Port': controller_port,
                  f'{IXNETWORK_CONTROLLER_MODEL}.User': 'admin',
                  f'{IXNETWORK_CONTROLLER_MODEL}.Password': 'DxTbqlSgAVPmrDLlHvJrsA==',
                  f'{IXNETWORK_CONTROLLER_MODEL}.License Server': '192.168.42.61'}
    init_context = test_helpers.service_init_command_context(IXNETWORK_CONTROLLER_MODEL, attributes)
    driver = IxNetworkController2GDriver()
    driver.initialize(init_context)
    print(driver.logger.handlers[0].baseFilename)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session: CloudShellAPISession, test_helpers: TestHelpers, server: list) -> ResourceCommandContext:
    controller_address, controller_port, _, ports = server
    attributes = [AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.Address', controller_address),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.Controller TCP Port', controller_port),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.User', 'admin'),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.Password', 'admin'),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.License Server', '192.168.42.61')]
    session.AddServiceToReservation(test_helpers.reservation_id, IXNETWORK_CONTROLLER_MODEL, ALIAS, attributes)
    context = test_helpers.resource_command_context(service_name=ALIAS)
    session.AddResourcesToReservation(test_helpers.reservation_id, ports)
    reservation_ports = get_resources_from_reservation(context, f'{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort',
                                                       f'{PERFECT_STORM_CHASSIS_MODEL}.GenericTrafficGeneratorPort')
    set_family_attribute(context, reservation_ports[0].Name, 'Logical Name', 'Port 1')
    set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Port 2')
    yield context


class TestIxNetworkControllerDriver:

    def test_load_config(self, driver: IxNetworkController2GDriver, context: ResourceCommandContext,
                         server: list) -> None:
        self._load_config(driver, context, server, 'test_config')

    def test_run_traffic(self, driver, context, server):
        self._load_config(driver, context, server, 'test_config')
        driver.send_arp(context)
        driver.start_protocols(context)
        time.sleep(8)
        driver.stop_traffic(context)
        driver.start_traffic(context, 'False')
        driver.stop_traffic(context)
        stats = driver.get_statistics(context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) >= 200)
        assert(int(stats['Port 1']['Frames Tx.']) <= 1800)
        driver.start_traffic(context, 'True')
        time.sleep(4)
        stats = driver.get_statistics(context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) >= 2000)
        stats = driver.get_statistics(context, 'Port Statistics', 'csv')
        driver.stop_protocols(context)
        print(stats)

    def test_run_quick_test(self, driver, context, server):
        self._load_config(driver, context, server, 'quick_test')
        quick_test_results = driver.run_quick_test(context, 'QuickTest1')
        print(quick_test_results)

    def test_negative(self, driver, context):
        reservation_ports = get_resources_from_reservation(context,
                                                           f'{PERFECT_STORM_CHASSIS_MODEL}.GenericTrafficGeneratorPort',
                                                           f'{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort')
        assert(len(reservation_ports) == 2)
        set_family_attribute(context, reservation_ports[0].Name, 'Logical Name', 'Port 1')
        set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', '')
        with pytest.raises(Exception):
            driver.load_config(context, path.join(path.dirname(__file__), 'test_config'))
        set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Port 1')
        with pytest.raises(Exception):
            driver.load_config(context, path.join(path.dirname(__file__), 'test_config'))
        set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Port x')
        with pytest.raises(Exception):
            driver.load_config(context, path.join(path.dirname(__file__), 'test_config'))
        # cleanup
        set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Port 2')

    def _load_config(self, driver, context, server, config_name):
        config_file = path.join(path.dirname(__file__), f'{config_name}_{server[2]}.ixncfg')
        driver.load_config(context, path.join(path.dirname(__file__), config_file))


class TestIxNetworkControllerShell:

    def test_session_id(self, session, context):
        session_id = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service', 'get_session_id')
        print(f'session_id = {session_id.Output[1:-1]}')
        root_obj = f'/{session_id.Output[1:-1]}/ixnetwork'
        print(f'root_obj = {root_obj}')

        globals = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                                         'get_children',
                                         [InputNameValue('obj_ref', root_obj),
                                          InputNameValue('child_type', 'globals')])
        print(f'globals = {globals.Output}')
        globals_obj = json.loads(globals.Output)[0]
        preferences = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                                             'get_children',
                                             [InputNameValue('obj_ref', globals_obj),
                                              InputNameValue('child_type', 'preferences')])
        print(f'preferences = {preferences.Output}')
        preferences_obj = json.loads(preferences.Output)[0]
        preferences_attrs = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                                                   'get_attributes',
                                                   [InputNameValue('obj_ref', preferences_obj)])
        print(f'preferences attributes = {preferences_attrs.Output}')

        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'set_attribute',
                               [InputNameValue('obj_ref', preferences_obj),
                                InputNameValue('attr_name', 'connectPortsOnLoadConfig'),
                                InputNameValue('attr_value', 'True')])
        preferences_attrs = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                                                   'get_attributes',
                                                   [InputNameValue('obj_ref', preferences_obj)])
        print(f'preferences attributes = {preferences_attrs.Output}')

    def test_load_config(self, session, context, server):
        self._load_config(session, context, ALIAS, server, 'test_config')

    def test_run_traffic(self, session, context, server):
        self._load_config(session, context, ALIAS, server, 'test_config')
        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'send_arp')
        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'start_protocols')
        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'stop_traffic')
        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'start_traffic', [InputNameValue('blocking', 'True')])
        stats = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                                       'get_statistics',
                                       [InputNameValue('view_name', 'Port Statistics'),
                                        InputNameValue('output_type', 'JSON')])
        assert int(json.loads(stats.Output)['Port 1']['Frames Tx.']) >= 2000

    def test_run_quick_test(self, session, context, server):
        self._load_config(session, context, ALIAS, server, 'quick_test')
        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'run_quick_test',
                               [InputNameValue('test', 'QuickTest1')])

    def _load_config(self, session, context, alias, server, config_name):
        config_file = path.join(path.dirname(__file__), f'{config_name}_{server[2]}.ixncfg')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'load_config',
                               [InputNameValue('config_file_location', config_file)])
