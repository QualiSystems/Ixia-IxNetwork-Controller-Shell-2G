"""
IxNetwork controller shell driver API. The business logic is implemented in ixn_handler.py.
"""
# pylint: disable=unused-argument
from typing import Union

from cloudshell.shell.core.driver_context import CancellationContext, InitCommandContext, ResourceCommandContext
from cloudshell.traffic.tg import TgControllerDriver, enqueue_keep_alive

from ixn_handler import IxnHandler


class IxNetworkController2GDriver(TgControllerDriver):
    """IxNetwork controller shell driver API."""

    def __init__(self) -> None:
        """Initialize object variables, actual initialization is performed in initialize method."""
        super().__init__()
        self.handler = IxnHandler()

    def initialize(self, context: InitCommandContext) -> None:
        """Initialize IxNetwork controller shell (from API)."""
        super().initialize(context)
        self.handler.initialize(context, self.logger)

    def cleanup(self) -> None:
        """Cleanup IxNetwork controller shell (from API)."""
        self.handler.cleanup()
        super().cleanup()

    def load_config(self, context: ResourceCommandContext, config_file_location: str) -> None:
        """Load configuration and reserve ports."""
        enqueue_keep_alive(context)
        self.handler.load_config(context, config_file_location)

    def send_arp(self, context: ResourceCommandContext) -> None:
        """Send ARP/ND for all interfaces (NA for Linux servers that supports only ngpf)."""
        self.handler.send_arp()

    def start_protocols(self, context: ResourceCommandContext) -> None:
        """Start all protocols (classic and ngpf) on all ports."""
        self.handler.start_protocols()

    def stop_protocols(self, context: ResourceCommandContext) -> None:
        """Stop all protocols (classic and ngpf) on all ports."""
        self.handler.stop_protocols()

    def start_traffic(self, context: ResourceCommandContext, blocking: str) -> None:
        """Start traffic on all ports."""
        self.handler.start_traffic(blocking)

    def stop_traffic(self, context: ResourceCommandContext) -> None:
        """Stop traffic on all ports."""
        self.handler.stop_traffic()

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

    def keep_alive(self, context: ResourceCommandContext, cancellation_context: CancellationContext) -> None:
        """Keep IxNetwork controller shell sessions alive (from TG controller API).

        Parent commands are not visible so we re re-define this method in child.
        """
        super().keep_alive(context, cancellation_context)

    #
    # Hidden commands for developers only.
    #

    def get_session_id(self, context: ResourceCommandContext) -> str:
        """Get REST session ID - API only command."""
        return self.handler.get_session_id()

    def get_children(self, context: ResourceCommandContext, obj_ref: str, child_type: str) -> list:
        """Get list of children - API only command."""
        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context: ResourceCommandContext, obj_ref: str) -> dict:
        """Get object attributes - API only command."""
        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context: ResourceCommandContext, obj_ref: str, attr_name: str, attr_value: str) -> None:
        """Set traffic generator object attribute - API only command."""
        self.handler.set_attribute(obj_ref, attr_name, attr_value)
