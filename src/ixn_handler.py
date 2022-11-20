"""
IxNetwork controller handler.
"""
import csv
import io
import json
import logging
from pathlib import Path
from typing import Optional, Union

from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.traffic.helpers import get_family_attribute, get_location, get_resources_from_reservation
from cloudshell.traffic.tg import IXIA_CHASSIS_MODEL, PERFECT_STORM_CHASSIS_MODEL, attach_stats_csv, is_blocking
from ixnetwork.ixn_app import IxnApp, init_ixn
from ixnetwork.ixn_statistics_view import IxnFlowStatistics, IxnPortStatistics, IxnStatisticsView, IxnTrafficItemStatistics
from trafficgenerator.tgn_utils import ApiType, TgnError

from ixn_data_model import IxNetwork_Controller_Shell_2G

IXIA_PORT_MODELS = [
    f"{PERFECT_STORM_CHASSIS_MODEL}.GenericTrafficGeneratorPort",
    f"{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort",
]


class IxnHandler:
    """IxNetwork controller shell business logic."""

    def __init__(self) -> None:
        """Initialize object variables, actual initialization is performed in initialize method."""
        self.ixn: IxnApp = None
        self.logger: logging.Logger = None

    def initialize(self, context: InitCommandContext, logger: logging.Logger) -> None:
        """Init IxnApp and connect to IxNetwork API server."""
        self.logger = logger

        service = IxNetwork_Controller_Shell_2G.create_from_context(context)

        self.ixn = init_ixn(ApiType.rest, self.logger)

        api_server = service.address if service.address else "localhost"
        api_port = service.controller_tcp_port if service.controller_tcp_port else "11009"
        if api_port == "443":
            user = service.user
            password = CloudShellSessionContext(context).get_api().DecryptPassword(service.password).Value
            auth = (user, password)
            if not service.license_server:
                service.license_server = "localhost"
        else:
            auth = None
        self.logger.debug(f"Connecting to API server {api_server} at {api_port} port with auth {auth}")
        self.ixn.connect(api_server=api_server, api_port=int(api_port), auth=auth)
        if service.license_server:
            self.ixn.api.set_licensing(licensing_servers=[service.license_server])

    def cleanup(self) -> None:
        """Release all ports and disconnect from IxNetwork API server."""
        for port in self.ixn.root.ports.values():
            port.release()
        self.ixn.disconnect()

    def load_config(self, context: ResourceCommandContext, ixia_config_file_name: str) -> None:
        """Load IxNetwork configuration file, and map and reserve ports."""
        self.ixn.load_config(Path(ixia_config_file_name))
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

    def send_arp(self) -> None:
        """Send ARP/ND for all devices and interfaces."""
        self.ixn.send_arp_ns()

    def start_protocols(self) -> None:
        """Start all protocols."""
        self.ixn.protocols_start()

    def stop_protocols(self) -> None:
        """Stop all protocols."""
        self.ixn.protocols_stop()

    def start_traffic(self, blocking: str) -> None:
        """Start traffic on all ports."""
        self.ixn.regenerate()
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start(is_blocking(blocking))

    def stop_traffic(self) -> None:
        """Start traffic on all ports."""
        self.ixn.l23_traffic_stop()

    def get_statistics(
        self, context: ResourceCommandContext, view_name: str, output_type: str, table_key: Optional[str]
    ) -> Union[dict, str]:
        """Get statistics for the requested view."""
        if view_name == "Port Statistics":
            stats_obj = IxnPortStatistics()
        elif view_name == "Traffic Item Statistics":
            stats_obj = IxnTrafficItemStatistics()
        elif view_name == "Flow Statistics":
            stats_obj = IxnFlowStatistics()
        else:
            stats_obj = IxnStatisticsView(view_name, table_key)

        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == "json":
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        if output_type.lower().strip() == "csv":
            output = io.StringIO()
            csv_writer = csv.DictWriter(output, stats_obj.captions)
            csv_writer.writeheader()
            for obj_name in statistics:
                csv_writer.writerow(statistics[obj_name])
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        raise TgnError(f'Output type should be CSV/JSON - got "{output_type}"')

    def run_quick_test(self, context: ResourceCommandContext, test: str) -> None:
        """Run quick test."""
        self.ixn.quick_test_apply(test)
        self.ixn.quick_test_start(test, blocking=True, timeout=3600 * 24)
        output = io.BytesIO()
        self.ixn.root.quick_tests[test].get_report(output)
        attach_stats_csv(context, self.logger, "quick_test", output.getvalue().strip(), suffix="pdf")

    def get_session_id(self) -> str:
        """Get REST session ID."""
        return self.ixn.api.session

    def get_children(self, obj_ref: str, child_type: str) -> list:
        """Get object attributes."""
        return self.ixn.api.getList(obj_ref, child_type)

    def get_attributes(self, obj_ref: str) -> dict:
        """Get object attributes."""
        return self.ixn.api.getAttributes(obj_ref)

    def set_attribute(self, obj_ref: str, attr_name: str, attr_value: str) -> None:
        """Set traffic generator object attribute."""
        self.ixn.api.setAttributes(obj_ref, **{attr_name: attr_value})
