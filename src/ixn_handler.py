"""
IxNetwork controller handler.
"""
import csv
import io
import json

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.traffic.helpers import get_family_attribute, get_location, get_resources_from_reservation
from cloudshell.traffic.tg import (
    IXIA_CHASSIS_MODEL,
    IXIA_VM_CHASSIS_MODEL,
    PERFECT_STORM_CHASSIS_MODEL,
    TgControllerHandler,
    attach_stats_csv,
    is_blocking,
)
from ixnetwork.ixn_app import init_ixn
from ixnetwork.ixn_statistics_view import IxnFlowStatistics, IxnStatisticsView
from trafficgenerator.tgn_utils import ApiType, TgnError

from ixn_data_model import IxNetwork_Controller_Shell_2G

IXIA_PORT_MODELS = [
    f"{PERFECT_STORM_CHASSIS_MODEL}.GenericTrafficGeneratorPort",
    f"{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort",
    f"{IXIA_VM_CHASSIS_MODEL}.VirtualTrafficGeneratorPort",
]


class IxnHandler(TgControllerHandler):
    def initialize(self, context, logger):

        service = IxNetwork_Controller_Shell_2G.create_from_context(context)
        super().initialize(context, logger, service)

        self.ixn = init_ixn(ApiType.rest, self.logger)

        api_server = self.service.address if self.service.address else "localhost"
        api_port = self.service.controller_tcp_port if self.service.controller_tcp_port else "11009"
        if api_port == "443":
            user = self.service.user
            password = CloudShellSessionContext(context).get_api().DecryptPassword(self.service.password).Value
            auth = (user, password)
            if not self.service.license_server:
                self.service.license_server = "localhost"
        else:
            auth = None
        self.logger.debug(f"Connecting to API server {api_server} at {api_port} port with auth {auth}")
        self.ixn.connect(api_server=api_server, api_port=int(api_port), auth=auth)
        if self.service.license_server:
            self.ixn.api.set_licensing(licensingServers=[self.service.license_server])

    def cleanup(self):
        for port in self.ixn.root.ports.values():
            port.release()
        self.ixn.disconnect()

    def load_config(self, context, ixia_config_file_name):

        self.ixn.load_config(ixia_config_file_name)
        config_ports = self.ixn.root.ports.values()

        for port in config_ports:
            port.release()

        reservation_ports = {}
        for port in get_resources_from_reservation(context, *IXIA_PORT_MODELS):
            reservation_ports[get_family_attribute(context, port.Name, "Logical Name").strip()] = port

        for port in config_ports:
            if port.name in reservation_ports:
                location = get_location(reservation_ports[port.name])
                self.logger.info(f"Logical Port {port.name} will be reserved on Physical location {location}")
                if "offline-debug" not in reservation_ports[port.name].Name.lower():
                    port.reserve(location, wait_for_up=False)
                else:
                    self.logger.debug(f"Offline debug port {location} - no actual reservation")
            else:
                raise TgnError(f'Configuration port "{port}" not found in reservation ports {reservation_ports.keys()}')

        for port in config_ports:
            if "offline-debug" not in reservation_ports[port.name].Name.lower():
                port.wait_for_states(40, "up")

        self.logger.info("Port Reservation Completed")

    def send_arp(self):
        self.ixn.send_arp_ns()

    def start_protocols(self):
        self.ixn.protocols_start()

    def stop_protocols(self):
        self.ixn.protocols_stop()

    def start_traffic(self, _, blocking):
        self.ixn.regenerate()
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start(is_blocking(blocking))

    def stop_traffic(self):
        self.ixn.l23_traffic_stop()

    def get_statistics(self, context, view_name, output_type):

        if view_name == "Flow Statistics":
            stats_obj = IxnFlowStatistics()
        else:
            stats_obj = IxnStatisticsView(view_name)

        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == "json":
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.lower().strip() == "csv":
            output = io.StringIO()
            w = csv.DictWriter(output, stats_obj.captions)
            w.writeheader()
            for obj_name in statistics:
                w.writerow(statistics[obj_name])
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise TgnError(f'Output type should be CSV/JSON - got "{output_type}"')

    def run_quick_test(self, context, test):
        self.ixn.quick_test_apply(test)
        self.ixn.quick_test_start(test, blocking=True, timeout=3600 * 24)
        output = io.BytesIO()
        self.ixn.root.quick_tests[test].get_report(output)
        attach_stats_csv(context, self.logger, "quick_test", output.getvalue().strip(), suffix="pdf")

    def get_session_id(self):
        return self.ixn.api.session

    def get_children(self, obj_ref, child_type):
        return self.ixn.api.getList(obj_ref, child_type)

    def get_attributes(self, obj_ref):
        return self.ixn.api.getAttributes(obj_ref)

    def set_attribute(self, obj_ref, attr_name, attr_value):
        return self.ixn.api.setAttributes(obj_ref, **{attr_name: attr_value})
