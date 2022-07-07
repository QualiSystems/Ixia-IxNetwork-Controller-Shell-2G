"""
IxNetwork controller shell driver API. The business logic is implemented in ixn_handler.py.
"""
# pylint: disable=unused-argument, arguments-differ
from typing import Union

from cloudshell.shell.core.driver_context import CancellationContext, InitCommandContext, ResourceCommandContext
from cloudshell.traffic.tg import TgControllerDriver

from ixn_handler import IxnHandler


class IxNetworkController2GDriver(TgControllerDriver):
    """IxNetwork controller shell driver API."""

    def __init__(self) -> None:
        """Initialize object variables, actual initialization is performed in initialize method."""
        super().__init__()
        self.handler = IxnHandler()

    def load_config(self, context: ResourceCommandContext, config_file_location: str) -> None:
        """Load configuration and reserve ports."""
        super().load_config(context, config_file_location)

    def send_arp(self, context: ResourceCommandContext) -> None:
        """Send ARP/ND for all interfaces (NA for Linux servers that supports only ngpf)."""
        super().send_arp(context)

    def start_protocols(self, context: ResourceCommandContext) -> None:
        """Start all protocols (classic and ngpf) on all ports."""
        super().start_protocols(context)

    def stop_protocols(self, context: ResourceCommandContext) -> None:
        """Stop all protocols (classic and ngpf) on all ports."""
        super().stop_protocols(context)

    def start_traffic(self, context: ResourceCommandContext, blocking: str) -> None:
        """Start traffic on all ports."""
        super().start_traffic(context, blocking)

    def stop_traffic(self, context: ResourceCommandContext) -> None:
        """Stop traffic on all ports."""
        super().stop_traffic(context)

    def get_statistics(
        self, context: ResourceCommandContext, view_name: str, output_type: str, table_key: str
    ) -> Union[dict, str]:
        """Get view statistics."""
        return self.handler.get_statistics(context, view_name, output_type, table_key)

    def run_quick_test(self, context: ResourceCommandContext, test: str) -> None:
        """Run quick test in blocking mode.

        :param test: name of quick test to run
        """
        self.handler.run_quick_test(context, test)

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context: InitCommandContext) -> None:
        """Initialize IxNetwork controller shell (from API)."""
        super().initialize(context)

    def cleanup(self) -> None:
        """Cleanup IxNetwork controller shell (from API)."""
        super().cleanup()

    def keep_alive(self, context: ResourceCommandContext, cancellation_context: CancellationContext) -> None:
        """Keep IxNetwork controller shell sessions alive (from TG controller API)."""
        super().keep_alive(context, cancellation_context)

    #
    # Hidden commands for developers only.
    #

    def get_session_id(self, context: ResourceCommandContext) -> str:
        """API only command to get REST session ID."""
        return self.handler.get_session_id()

    def get_children(self, context: ResourceCommandContext, obj_ref: str, child_type: str) -> list:
        """API only command to get list of children.

        :param str obj_ref: valid object reference
        :param str child_type: requested children type. If None returns all children
        :return: list(object references of children)
        """
        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context: ResourceCommandContext, obj_ref: str) -> dict:
        """API only command to get object attributes.

        :param str obj_ref: valid object reference
        :return: dict(key, values) of all attributes
        """
        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context: ResourceCommandContext, obj_ref: str, attr_name: str, attr_value: str) -> None:
        """API only command to set traffic generator object attribute.

        :param str obj_ref: valid object reference
        :param str attr_name: attribute name
        :param str attr_value: attribute value
        """
        self.handler.set_attribute(obj_ref, attr_name, attr_value)
