
from os import path
import time
import pytest
import json

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.helpers import (set_family_attribute, get_reservation_id, get_resources_from_reservation,
                                        add_resources_to_reservation)
from cloudshell.traffic.tg import IXNETWORK_CONTROLLER_MODEL
from shellfoundry.releasetools.test_helper import (create_init_command_context, create_session_from_deployment,
                                                   create_service_command_context, end_reservation)

from src.ixn_driver import IxNetworkController2GDriver

ports_840 = ['IxVM 8.40 1/Module1/Port2', 'IxVM 8.40 2/Module1/Port1']
ports_850 = ['ixia-850-1/Module1/Port2', 'ixia-850-1/Module1/Port1']
ports_900 = ['ixia-900-1/Module1/Port2', 'ixia-900-1/Module1/Port1']

linux_840 = '192.168.65.27:443'
linux_850 = '192.168.65.73:443'
linux_900 = '192.168.65.27:443'

windows_801 = '192.168.65.39:11009'
windows_840 = '192.168.65.68:11009'
windows_850 = '192.168.65.94:11009'
windows_900 = 'localhost:11009'

cm_900 = '192.168.42.199:443'


server_properties = {linux_840: {'ports': ports_840, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_850: {'ports': ports_850, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_900: {'ports': ports_900, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     windows_840: {'ports': ports_840, 'auth': None, 'config_version': 'classic'},
                     windows_850: {'ports': ports_850, 'auth': None, 'config_version': 'classic'},
                     windows_900: {'ports': ports_900, 'auth': None, 'config_version': 'classic'},
                     cm_900: {'ports': ports_900, 'auth': None, 'config_version': 'classic'}}


@pytest.fixture()
def alias():
    yield 'IxNetwork Controller'


# @pytest.fixture(params=[windows_900_http, linux_900],
#                 ids=['windows-900-http', 'linux-900'])
@pytest.fixture(params=[windows_900])
def server(request):
    controller_address = request.param.split(':')[0]
    controller_port = request.param.split(':')[1]
    config_version = server_properties[request.param]['config_version']
    ports = server_properties[request.param]['ports']
    yield controller_address, controller_port, config_version, ports


@pytest.fixture()
def session():
    yield create_session_from_deployment()


@pytest.fixture()
def driver(session, server):
    controller_address, controller_port, _, _ = server
    attributes = {f'{IXNETWORK_CONTROLLER_MODEL}.Address': controller_address,
                  f'{IXNETWORK_CONTROLLER_MODEL}.Controller TCP Port': controller_port,
                  f'{IXNETWORK_CONTROLLER_MODEL}.User': 'admin',
                  f'{IXNETWORK_CONTROLLER_MODEL}.Password': 'DxTbqlSgAVPmrDLlHvJrsA==',
                  f'{IXNETWORK_CONTROLLER_MODEL}.License Server': '192.168.42.61'}
    init_context = create_init_command_context(session, 'CS_TrafficGeneratorController', IXNETWORK_CONTROLLER_MODEL,
                                               controller_address, attributes, 'Service')
    driver = IxNetworkController2GDriver()
    driver.initialize(init_context)
    print(driver.logger.handlers[0].baseFilename)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session, alias, server):
    controller_address, controller_port, _, ports = server
    attributes = [AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.Address', controller_address),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.Controller TCP Port', controller_port),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.User', 'admin'),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.Password', 'admin'),
                  AttributeNameValue(f'{IXNETWORK_CONTROLLER_MODEL}.License Server', '192.168.42.61')]
    context = create_service_command_context(session, IXNETWORK_CONTROLLER_MODEL, alias, attributes)
    add_resources_to_reservation(context, *ports)
    reservation_ports = get_resources_from_reservation(context,
                                                       'Generic Traffic Generator Port',
                                                       'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                       'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
    set_family_attribute(context, reservation_ports[0].Name, 'Logical Name', 'Port 1')
    set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Port 2')
    yield context
    end_reservation(session, get_reservation_id(context))


class TestIxNetworkControllerDriver:

    def test_load_config(self, driver, context, server):
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
                                                           'Generic Traffic Generator Port',
                                                           'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                           'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
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
        config_file = path.join(path.dirname(__file__), '{}_{}.ixncfg'.format(config_name, server[2]))
        driver.load_config(context, path.join(path.dirname(__file__), config_file))


class TestIxNetworkControllerShell:

    def test_session_id(self, session, context, alias):
        session_id = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                            'get_session_id')
        print('session_id = {}'.format(session_id.Output[1:-1]))
        root_obj = '/{}/ixnetwork'.format(session_id.Output[1:-1])
        print('root_obj = {}'.format(root_obj))

        globals = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                         'get_children',
                                         [InputNameValue('obj_ref', root_obj),
                                          InputNameValue('child_type', 'globals')])
        print('globals = {}'.format(globals.Output))
        globals_obj = json.loads(globals.Output)[0]
        prefs = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                       'get_children',
                                       [InputNameValue('obj_ref', globals_obj),
                                        InputNameValue('child_type', 'preferences')])
        print('preferences = {}'.format(prefs.Output))
        prefs_obj = json.loads(prefs.Output)[0]
        prefs_attrs = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                             'get_attributes',
                                             [InputNameValue('obj_ref', prefs_obj)])
        print('preferences attributes = {}'.format(prefs_attrs.Output))

        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'set_attribute',
                               [InputNameValue('obj_ref', prefs_obj),
                                InputNameValue('attr_name', 'connectPortsOnLoadConfig'),
                                InputNameValue('attr_value', 'True')])
        prefs_attrs = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                             'get_attributes',
                                             [InputNameValue('obj_ref', prefs_obj)])
        print('preferences attributes = {}'.format(prefs_attrs.Output))

    def test_load_config(self, session, context, alias, server):
        self._load_config(session, context, alias, server, 'test_config')

    def test_run_traffic(self, session, context, alias, server):
        self._load_config(session, context, alias, server, 'test_config')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'send_arp')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'start_protocols')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'stop_traffic')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'start_traffic', [InputNameValue('blocking', 'True')])
        stats = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                       'get_statistics',
                                       [InputNameValue('view_name', 'Port Statistics'),
                                        InputNameValue('output_type', 'JSON')])
        assert int(json.loads(stats.Output)['Port 1']['Frames Tx.']) >= 2000

    def test_run_quick_test(self, session, context, alias, server):
        self._load_config(session, context, alias, server, 'quick_test')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'run_quick_test',
                               [InputNameValue('test', 'QuickTest1')])

    def _load_config(self, session, context, alias, server, config_name):
        config_file = path.join(path.dirname(__file__), '{}_{}.ixncfg'.format(config_name, server[2]))
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'load_config',
                               [InputNameValue('config_file_location', config_file)])
