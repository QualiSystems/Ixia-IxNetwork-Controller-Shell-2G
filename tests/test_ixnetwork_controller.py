
from os import path
import time
import pytest
import json

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.common import add_resources_to_reservation, get_reservation_id, get_resources_from_reservation
from cloudshell.traffic.tg_helper import set_family_attribute
from cloudshell.traffic.tg import IXNETWORK_CONTROLLER_MODEL
from shellfoundry.releasetools.test_helper import (create_init_command_context, create_session_from_deployment,
                                                   create_service_command_context, end_reservation)

from src.ixia_driver import IxNetworkController2GDriver

ports_840 = ['IxVM 8.40 1/Module1/Port2', 'IxVM 8.40 2/Module1/Port1']
ports_850 = ['ixia-850-1/Module1/Port2', 'ixia-850-1/Module1/Port1']
ports_900 = ['ixia-900-1/Module1/Port2', 'ixia-900-1/Module1/Port1']

linux_840 = '192.168.65.27:443'
linux_850 = '192.168.65.73:443'
linux_900 = '192.168.65.55:443'

windows_801 = '192.168.65.39:11009'
windows_840 = '192.168.65.68:11009'
windows_850 = '192.168.65.94:11009'
windows_900_http = 'localhost:11009'
windows_900_https = '192.168.65.25:11009'

cm_900 = '192.168.42.199:443'


server_properties = {linux_840: {'ports': ports_840, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_850: {'ports': ports_850, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_900: {'ports': ports_900, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     windows_840: {'ports': ports_840, 'auth': None, 'config_version': 'classic'},
                     windows_850: {'ports': ports_850, 'auth': None, 'config_version': 'classic'},
                     windows_900_http: {'ports': ports_900, 'auth': None, 'config_version': 'classic'},
                     windows_900_https: {'ports': ports_900, 'auth': None, 'config_version': 'classic'},
                     cm_900: {'ports': ports_900, 'auth': None, 'config_version': 'classic'}}

server  = windows_900_http

controller = server.split(':')[0]
port = server.split(':')[1]
config_version = server_properties[server]['config_version']
ports = server_properties[server]['ports']


@pytest.fixture()
def model():
    yield IXNETWORK_CONTROLLER_MODEL


@pytest.fixture()
def alias():
    yield 'IxNetwork Controller'


@pytest.fixture(params=[(controller, port)],
                ids=['windows-900'])
def dut(request):
    yield request.param


@pytest.fixture()
def session():
    yield create_session_from_deployment()


@pytest.fixture()
def driver(session, model, dut):
    controller_address, controller_port = dut
    attributes = {model + '.Address': controller_address,
                  model + '.Controller TCP Port': controller_port,
                  model + '.User': 'admin',
                  model + '.Password': 'DxTbqlSgAVPmrDLlHvJrsA==',
                  model + '.License Server': '192.168.42.61'}
    init_context = create_init_command_context(session, 'CS_TrafficGeneratorController', model, 'na', attributes,
                                               'Service')
    driver = IxNetworkController2GDriver()
    driver.initialize(init_context)
    print(driver.logger.handlers[0].baseFilename)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session, model, alias, dut):
    controller_address, controller_port = dut
    attributes = [AttributeNameValue(model + '.Address', controller_address),
                  AttributeNameValue(model + '.Controller TCP Port', controller_port),
                  AttributeNameValue(model + '.User', 'admin'),
                  AttributeNameValue(model + '.Password', 'admin'),
                  AttributeNameValue(model + '.License Server', '192.168.42.61')]
    context = create_service_command_context(session, model, alias, attributes)
    add_resources_to_reservation(context, *ports)
    yield context
    end_reservation(session, get_reservation_id(context))


def load_config(context, config_name, driver=None, session=None, alias=None):
    config_file = path.join(path.dirname(__file__), '{}_{}.ixncfg'.format(config_name, config_version))
    reservation_ports = get_resources_from_reservation(context, 'Generic Traffic Generator Port',
                                                       'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                       'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
    set_family_attribute(context, reservation_ports[0], 'Logical Name', 'Port 1')
    set_family_attribute(context, reservation_ports[1], 'Logical Name', 'Port 2')
    if driver:
        driver.load_config(context, path.join(path.dirname(__file__), config_file))
    else:
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'load_config',
                               [InputNameValue('config_file_location', config_file)])


class TestIxNetworkControllerDriver(object):

    def test_load_config(self, driver, context):
        load_config(context, 'test_config', driver=driver)

    def test_run_traffic(self, driver, context):
        load_config(context, 'test_config', driver=driver)
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
        time.sleep(2)
        stats = driver.get_statistics(context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) >= 2000)
        stats = driver.get_statistics(context, 'Port Statistics', 'csv')
        driver.stop_protocols(context)
        print(stats)

    def test_run_quick_test(self, driver, context):
        load_config(context, 'quick_test', driver=driver)
        quick_test_results = driver.run_quick_test(context, 'QuickTest1')
        print(quick_test_results)

    def negative_tests(self, driver, context):
        reservation_ports = get_resources_from_reservation(context,
                                                           'Generic Traffic Generator Port',
                                                           'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                           'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        assert(len(reservation_ports) == 2)
        set_family_attribute(context, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(context, reservation_ports[1], 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config'))
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 1')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config'))
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config'))
        # cleanup
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')


class TestIxNetworkControllerShell(object):

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

    def test_load_config(self, session, context, alias):
        load_config(context, 'test_config', session=session, alias=alias)

    def test_run_traffic(self, session, context, alias):
        load_config(context, 'test_config', session=session, alias=alias)
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
        assert(int(json.loads(stats.Output)['Port 1']['Frames Tx.']) >= 2000)

    def test_run_quick_test(self, session, context, alias):
        load_config(context, 'quick_test', session=session, alias=alias)
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'run_quick_test',
                               [InputNameValue('test', 'QuickTest1')])
