"""Construct SSH command/API parameters from validated query data.

Accepts filtered & validated input from execute.py, constructs SSH
command for Netmiko library or API call parameters for supported
hyperglass API modules.
"""

# Standard Library Imports
import ipaddress
import json
import operator
import re

# Project Imports
from hyperglass.configuration import commands
from hyperglass.constants import target_format_space
from hyperglass.exceptions import HyperglassError
from hyperglass.util import log


class Construct:
    """Construct SSH commands/REST API parameters from validated query data."""

    def get_device_vrf(self):
        """Match query VRF to device VRF.

        Raises:
            HyperglassError: Raised if VRFs do not match.

        Returns:
            {object} -- Matched VRF object
        """
        _device_vrf = None
        for vrf in self.device.vrfs:
            if vrf.name == self.query_vrf:
                _device_vrf = vrf
        if not _device_vrf:
            raise HyperglassError(
                message="Unable to match query VRF to any configured VRFs",
                alert="danger",
                keywords=[self.query_vrf],
            )
        return _device_vrf

    def __init__(self, device, query_data, transport):
        """Initialize command construction.

        Arguments:
            device {object} -- Device object
            query_data {object} -- Validated query object
            transport {str} -- Transport name; 'scrape' or 'rest'
        """
        self.device = device
        self.query_data = query_data
        self.transport = transport
        self.query_target = self.query_data.query_target
        self.query_vrf = self.query_data.query_vrf
        self.device_vrf = self.get_device_vrf()

    def format_target(self, target):
        """Format query target based on NOS requirement.

        Arguments:
            target {str} -- Query target

        Returns:
            {str} -- Formatted target
        """
        if self.device.nos in target_format_space:
            _target = re.sub(r"\/", r" ", target)
        else:
            _target = target
        target_string = str(_target)
        log.debug(f"Formatted target: {target_string}")
        return target_string

    @staticmethod
    def device_commands(nos, afi, query_type):
        """Construct class attribute path for device commansd.

        This is required because class attributes are set dynamically
        when devices.yaml is imported, so the attribute path is unknown
        until runtime.

        Arguments:
            nos {str} -- NOS short name
            afi {str} -- Address family
            query_type {str} -- Query type

        Returns:
            {str} -- Dotted attribute path, e.g. 'cisco_ios.ipv4.bgp_route'
        """
        cmd_path = f"{nos}.{afi}.{query_type}"
        return operator.attrgetter(cmd_path)(commands)

    @staticmethod
    def get_cmd_type(query_protocol, query_vrf):
        """Construct AFI string.

        If query_vrf is specified, AFI prefix is "vpnv".
        If not, AFI prefix is "ipv".

        Arguments:
            query_protocol {str} -- 'ipv4' or 'ipv6'
            query_vrf {str} -- Query VRF name

        Returns:
            {str} -- Constructed command name
        """
        if query_vrf and query_vrf != "default":
            cmd_type = f"{query_protocol}_vpn"
        else:
            cmd_type = f"{query_protocol}_default"
        return cmd_type

    def ping(self):
        """Construct ping query parameters from pre-validated input.

        Returns:
            {str} -- SSH command or stringified JSON
        """
        log.debug(
            f"Constructing ping query for {self.query_target} via {self.transport}"
        )

        query = []
        query_protocol = f"ipv{ipaddress.ip_network(self.query_target).version}"
        afi = getattr(self.device_vrf, query_protocol)
        cmd_type = self.get_cmd_type(query_protocol, self.query_vrf)

        if self.transport == "rest":
            query.append(
                json.dumps(
                    {
                        "query_type": "ping",
                        "vrf": afi.vrf_name,
                        "afi": cmd_type,
                        "source": afi.source_address.compressed,
                        "target": self.query_target,
                    }
                )
            )
        elif self.transport == "scrape":
            cmd = self.device_commands(self.device.commands, cmd_type, "ping")
            query.append(
                cmd.format(
                    target=self.query_target,
                    source=afi.source_address,
                    vrf=afi.vrf_name,
                )
            )

        log.debug(f"Constructed query: {query}")
        return query

    def traceroute(self):
        """Construct traceroute query parameters from pre-validated input.

        Returns:
            {str} -- SSH command or stringified JSON
        """
        log.debug(
            (
                f"Constructing traceroute query for {self.query_target} "
                f"via {self.transport}"
            )
        )

        query = []
        query_protocol = f"ipv{ipaddress.ip_network(self.query_target).version}"
        afi = getattr(self.device_vrf, query_protocol)
        cmd_type = self.get_cmd_type(query_protocol, self.query_vrf)

        if self.transport == "rest":
            query.append(
                json.dumps(
                    {
                        "query_type": "traceroute",
                        "vrf": afi.vrf_name,
                        "afi": cmd_type,
                        "source": afi.source_address.compressed,
                        "target": self.query_target,
                    }
                )
            )
        elif self.transport == "scrape":
            cmd = self.device_commands(self.device.commands, cmd_type, "traceroute")
            query.append(
                cmd.format(
                    target=self.query_target,
                    source=afi.source_address,
                    vrf=afi.vrf_name,
                )
            )

        log.debug(f"Constructed query: {query}")
        return query

    def bgp_route(self):
        """Construct bgp_route query parameters from pre-validated input.

        Returns:
            {str} -- SSH command or stringified JSON
        """
        log.debug(
            f"Constructing bgp_route query for {self.query_target} via {self.transport}"
        )

        query = []
        query_protocol = f"ipv{ipaddress.ip_network(self.query_target).version}"
        afi = getattr(self.device_vrf, query_protocol)
        cmd_type = self.get_cmd_type(query_protocol, self.query_vrf)

        if self.transport == "rest":
            query.append(
                json.dumps(
                    {
                        "query_type": "bgp_route",
                        "vrf": afi.vrf_name,
                        "afi": cmd_type,
                        "source": None,
                        "target": self.format_target(self.query_target),
                    }
                )
            )
        elif self.transport == "scrape":
            cmd = self.device_commands(self.device.commands, cmd_type, "bgp_route")
            query.append(
                cmd.format(
                    target=self.format_target(self.query_target),
                    source=afi.source_address,
                    vrf=afi.vrf_name,
                )
            )

        log.debug(f"Constructed query: {query}")
        return query

    def bgp_community(self):
        """Construct bgp_community query parameters from pre-validated input.

        Returns:
            {str} -- SSH command or stringified JSON
        """
        log.debug(
            (
                f"Constructing bgp_community query for "
                f"{self.query_target} via {self.transport}"
            )
        )

        query = []
        afis = []

        for vrf_key, vrf_value in {
            p: e for p, e in self.device_vrf.dict().items() if p in ("ipv4", "ipv6")
        }.items():
            if vrf_value:
                afis.append(vrf_key)

        for afi in afis:
            afi_attr = getattr(self.device_vrf, afi)
            cmd_type = self.get_cmd_type(afi, self.query_vrf)
            if self.transport == "rest":
                query.append(
                    json.dumps(
                        {
                            "query_type": "bgp_community",
                            "vrf": afi_attr.vrf_name,
                            "afi": cmd_type,
                            "target": self.query_target,
                            "source": None,
                        }
                    )
                )
            elif self.transport == "scrape":
                cmd = self.device_commands(
                    self.device.commands, cmd_type, "bgp_community"
                )
                query.append(
                    cmd.format(
                        target=self.query_target,
                        source=afi_attr.source_address,
                        vrf=afi_attr.vrf_name,
                    )
                )

        log.debug(f"Constructed query: {query}")
        return query

    def bgp_aspath(self):
        """Construct bgp_aspath query parameters from pre-validated input.

        Returns:
            {str} -- SSH command or stringified JSON
        """
        log.debug(
            (
                f"Constructing bgp_aspath query for "
                f"{self.query_target} via {self.transport}"
            )
        )

        query = []
        afis = []

        for vrf_key, vrf_value in {
            p: e for p, e in self.device_vrf.dict().items() if p in ("ipv4", "ipv6")
        }.items():
            if vrf_value:
                afis.append(vrf_key)

        for afi in afis:
            afi_attr = getattr(self.device_vrf, afi)
            cmd_type = self.get_cmd_type(afi, self.query_vrf)
            if self.transport == "rest":
                query.append(
                    json.dumps(
                        {
                            "query_type": "bgp_aspath",
                            "vrf": afi_attr.vrf_name,
                            "afi": cmd_type,
                            "target": self.query_target,
                            "source": None,
                        }
                    )
                )
            elif self.transport == "scrape":
                cmd = self.device_commands(self.device.commands, cmd_type, "bgp_aspath")
                query.append(
                    cmd.format(
                        target=self.query_target,
                        source=afi_attr.source_address,
                        vrf=afi_attr.vrf_name,
                    )
                )

        log.debug(f"Constructed query: {query}")
        return query