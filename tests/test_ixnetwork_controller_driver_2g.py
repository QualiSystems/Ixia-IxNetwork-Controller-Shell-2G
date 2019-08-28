
from os import path
import sys
import logging
import time

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_deployment, create_command_context

from src.driver import IxNetworkControllerShell2GDriver
import test_ixnetwork_configs

server  = test_ixnetwork_configs.cm_90

controller = server.split(':')[0]
port = server.split(':')[1]
config_version = test_ixnetwork_configs.server_properties[server]['config_version']
ports = test_ixnetwork_configs.server_properties[server]['ports']

attributes = {'IxNetwork Controller Shell 2G.Address': controller,
              'IxNetwork Controller Shell 2G.Controller TCP Port': port,
              'IxNetwork Controller Shell 2G.User': 'admin',
              'IxNetwork Controller Shell 2G.Password': 'DxTbqlSgAVPmrDLlHvJrsA==',
              'IxNetwork Controller Shell 2G.License Server': '192.168.42.61'}


class TestIxNetworkControllerDriver(object):

    def setup(self):
        self.session = create_session_from_deployment()
        self.context = create_command_context(self.session, ports, 'IxNetwork Controller', attributes)
        self.driver = IxNetworkControllerShell2GDriver()
        self.driver.initialize(self.context)
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.driver.logger.info('logfile = {}'.format(self.driver.logger.handlers[0].baseFilename))

    def teardown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        self._load_config('test_config')

    def test_run_traffic(self):
        self._load_config('test_config')
        self.driver.send_arp(self.context)
        self.driver.start_protocols(self.context)
        time.sleep(8)
        self.driver.stop_traffic(self.context)
        self.driver.start_traffic(self.context, 'False')
        self.driver.stop_traffic(self.context)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) >= 200)
        assert(int(stats['Port 1']['Frames Tx.']) <= 1800)
        self.driver.start_traffic(self.context, 'True')
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) >= 2000)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'csv')
        print(stats)

    def negative_tests(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        assert(len(reservation_ports) == 2)
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', '')
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

    def test_run_quick_test(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')
        self._load_config(path.join(path.dirname(__file__), 'quick_test'))
        print self.driver.run_quick_test(self.context, 'QuickTest1')

    def _load_config(self, config_name):
        config_file = path.join(path.dirname(__file__), '{}_{}.ixncfg'.format(config_name, config_version))
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), config_file))
