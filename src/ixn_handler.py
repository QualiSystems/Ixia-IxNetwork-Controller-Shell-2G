import json
import csv
import io

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.traffic.handler import TrafficHandler
from cloudshell.traffic.tg_helper import (get_reservation_resources, get_address, is_blocking, attach_stats_csv,
                                          get_family_attribute)

from trafficgenerator.tgn_utils import ApiType
from ixnetwork.ixn_app import init_ixn
from ixnetwork.ixn_statistics_view import IxnStatisticsView, IxnFlowStatistics


class IxnHandler(TrafficHandler):

    def __init__(self, shell_name=""):
        super(IxnHandler, self).__init__()
        self.namespace = "{}.".format(shell_name) if shell_name else ""

    def initialize(self, context, logger):

        self.logger = logger

        tcl_server = context.resource.attributes['{}Address'.format(self.namespace)]
        tcl_port = context.resource.attributes['{}Controller TCP Port'.format(self.namespace)]

        self.ixn = init_ixn(ApiType.rest, self.logger)

        if tcl_server.lower() in ('na', ''):
            tcl_server = 'localhost'
        if not tcl_port:
            tcl_port = 11009
        self.logger.debug("connecting to tcl server {} at {} port".format(tcl_server, tcl_port))
        self.ixn.connect(tcl_server=tcl_server, tcl_port=tcl_port)

    def tearDown(self):
        for port in self.ixn.root.get_objects_by_type('vport'):
            port.release()
        self.ixn.disconnect()

    def load_config(self, context, ixia_config_file_name):

        self.ixn.load_config(ixia_config_file_name)
        config_ports = self.ixn.root.get_children('vport')

        for port in config_ports:
            port.release()

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        reservation_ports = {}
        for port in get_reservation_resources(my_api, reservation_id,
                                              'Generic Traffic Generator Port',
                                              'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                              'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort'):
            reservation_ports[get_family_attribute(my_api, port, 'Logical Name').Value.strip()] = port

        for port in config_ports:
            name = port.obj_name()
            if name in reservation_ports:
                address = get_address(reservation_ports[name])
                self.logger.debug('Logical Port {} will be reserved on Physical location {}'.format(name, address))
                port.reserve(address, wait_for_up=False)
            else:
                self.logger.error('Configuration port "{}" not found in reservation ports {}'.
                                  format(port, reservation_ports.keys()))
                raise Exception('Configuration port "{}" not found in reservation ports {}'.
                                format(port, reservation_ports.keys()))

        for port in config_ports:
            port.wait_for_states(40, 'up')

        self.logger.info("Port Reservation Completed")

    def send_arp(self):
        self.ixn.send_arp_ns()

    def start_protocols(self):
        self.ixn.protocols_start()

    def stop_protocols(self):
        self.ixn.protocols_stop()

    def start_traffic(self, blocking):
        self.ixn.regenerate()
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start(is_blocking(blocking))

    def stop_traffic(self):
        self.ixn.l23_traffic_stop()

    def get_statistics(self, context, view_name, output_type):

        if view_name == 'Flow Statistics':
            stats_obj = IxnFlowStatistics(self.ixn.root)
        else:
            stats_obj = IxnStatisticsView(self.ixn.root, view_name)

        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.lower().strip() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, stats_obj.captions)
            w.writeheader()
            for obj_name in statistics:
                w.writerow(statistics[obj_name])
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON - got "{}"'.format(output_type))

    def run_quick_test(self, context, test):

        self.ixn.quick_test_apply(test)
        return self.ixn.quick_test_start(test, blocking=True, timeout=3600 * 24)

    def get_session_id(self):
        return self.ixn.api.session

    def get_children(self, obj_ref, child_type):
        return self.ixn.api.getList(obj_ref, child_type)

    def get_attributes(self, obj_ref):
        return self.ixn.api.getAttributes(obj_ref)

    def set_attribute(self, obj_ref, attr_name, attr_value):
        return self.ixn.api.setAttributes(obj_ref, **{attr_name: attr_value})
