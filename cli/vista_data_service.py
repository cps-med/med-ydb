# -----------------------------------------------------------
# app/vista_data_service.py
# -----------------------------------------------------------

"""
VistA Data Service - Simulates JLV's VistaDataService component

This module demonstrates the pattern JLV uses to make RPC calls to VistA sites.
In production, JLV uses the RPC Broker protocol over TCP. This simulation uses
direct M routine calls via YottaDB for educational purposes.

Design pattern:
1. VistaSite: Represents a connection to a VistA instance
2. RPCCall: Encapsulates an RPC request
3. RPCResult: Encapsulates an RPC response
4. VistaDataService: Coordinates RPC execution across sites

To run:
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/vista_data_service.py'

Note: This is an EDUCATIONAL SIMULATION. Real JLV:
- Uses Java, not Python
- Connects via RPC Broker protocol (TCP port 9430)
- Handles authentication, context, and security
- Aggregates data from MULTIPLE VistA sites
- Has sophisticated caching and error handling
"""

import sys
from typing import Any, Dict, List, Optional

import yottadb
from yottadb import YDBError


class VistaSite:
    """
    Represents a VistA site/station.

    In real JLV, each site has:
    - Station number (3-digit VA facility code)
    - Hostname/IP
    - Port (usually 9430)
    - Connection pool

    This simulation represents a single VEHU instance.
    """

    def __init__(self, site_code, name, description=""):
        # type: (str, str, str) -> None
        """
        Initialize a VistA site.

        Args:
            site_code: Site identifier (e.g., "500" for VHA station)
            name: Human-readable name (e.g., "VEHU Development")
            description: Optional description
        """
        self.site_code = site_code
        self.name = name
        self.description = description
        self.connected = False

    def connect(self):
        # type: () -> bool
        """
        Simulate connecting to VistA site.

        In real JLV: Opens RPC Broker connection, authenticates
        In simulation: Just checks YottaDB is accessible
        """
        try:
            # Test YottaDB access
            yottadb.get("$ZYRELEASE")
            self.connected = True
            return True
        except Exception as e:
            print("Error connecting to site {}: {}".format(self.site_code, e), file=sys.stderr)
            self.connected = False
            return False

    def disconnect(self):
        # type: () -> None
        """Disconnect from site."""
        self.connected = False

    def __repr__(self):
        # type: () -> str
        status = "connected" if self.connected else "disconnected"
        return "VistaSite(code={}, name={}, status={})".format(
            self.site_code, self.name, status
        )


class RPCCall:
    """
    Encapsulates an RPC request.

    In real JLV, this includes:
    - RPC name
    - Parameters
    - Context (menu option)
    - Timeout settings
    """

    def __init__(self, rpc_name, params=None):
        # type: (str, Optional[List[str]]) -> None
        """
        Create an RPC call request.

        Args:
            rpc_name: Name of RPC (e.g., "ORWPT SELECT")
            params: List of parameter values
        """
        self.rpc_name = rpc_name
        self.params = params if params is not None else []

    def __repr__(self):
        # type: () -> str
        return "RPCCall(rpc={}, params={})".format(self.rpc_name, self.params)


class RPCResult:
    """
    Encapsulates an RPC response.

    Includes:
    - Success/failure status
    - Return value (single value or array)
    - Error message if failed
    - Metadata (site, timing, etc.)
    """

    def __init__(self, success, value=None, error=None, site_code=None):
        # type: (bool, Any, Optional[str], Optional[str]) -> None
        """
        Create an RPC result.

        Args:
            success: Whether RPC succeeded
            value: Return value (string, list, dict, etc.)
            error: Error message if failed
            site_code: Which site returned this result
        """
        self.success = success
        self.value = value
        self.error = error
        self.site_code = site_code

    def __repr__(self):
        # type: () -> str
        if self.success:
            value_preview = str(self.value)[:50]
            return "RPCResult(success=True, value={})".format(value_preview)
        else:
            return "RPCResult(success=False, error={})".format(self.error)


class VistaDataService:
    """
    VistA Data Service - coordinates RPC calls to VistA sites.

    This simulates JLV's VistaDataService component which:
    - Manages connections to multiple VistA sites
    - Executes RPC calls
    - Handles errors and retries
    - Aggregates results from multiple sites

    In this simulation, we only have one VEHU site, but the pattern
    is designed to support multiple sites.
    """

    def __init__(self):
        # type: () -> None
        """Initialize the data service."""
        self.sites = {}  # type: Dict[str, VistaSite]

    def register_site(self, site):
        # type: (VistaSite) -> None
        """
        Register a VistA site.

        Args:
            site: VistaSite instance
        """
        self.sites[site.site_code] = site

    def connect_all_sites(self):
        # type: () -> Dict[str, bool]
        """
        Connect to all registered sites.

        Returns:
            Dict mapping site_code → connection success
        """
        results = {}
        for site_code, site in self.sites.items():
            results[site_code] = site.connect()
        return results

    def execute_rpc(self, site_code, rpc_call):
        # type: (str, RPCCall) -> RPCResult
        """
        Execute an RPC on a specific site.

        Args:
            site_code: Which site to call
            rpc_call: RPC request to execute

        Returns:
            RPCResult with response or error
        """
        # Check site exists and is connected
        if site_code not in self.sites:
            return RPCResult(
                success=False,
                error="Site {} not registered".format(site_code),
                site_code=site_code
            )

        site = self.sites[site_code]
        if not site.connected:
            return RPCResult(
                success=False,
                error="Site {} not connected".format(site_code),
                site_code=site_code
            )

        # Execute the RPC
        # In real JLV: Would use RPC Broker protocol
        # In simulation: Call M routine directly
        try:
            result_value = self._simulate_rpc_call(rpc_call)
            return RPCResult(
                success=True,
                value=result_value,
                site_code=site_code
            )
        except Exception as e:
            return RPCResult(
                success=False,
                error="RPC execution failed: {}".format(str(e)),
                site_code=site_code
            )

    def execute_rpc_all_sites(self, rpc_call):
        # type: (RPCCall) -> Dict[str, RPCResult]
        """
        Execute an RPC on ALL registered sites.

        This is the key JLV pattern: query multiple VistA sites
        and aggregate results.

        Args:
            rpc_call: RPC request to execute

        Returns:
            Dict mapping site_code → RPCResult
        """
        results = {}
        for site_code in self.sites.keys():
            results[site_code] = self.execute_rpc(site_code, rpc_call)
        return results

    def _simulate_rpc_call(self, rpc_call):
        # type: (RPCCall) -> Any
        """
        Simulate executing an RPC by looking up and calling M routine.

        This is SIMULATION ONLY. Real JLV uses RPC Broker protocol.

        Args:
            rpc_call: RPC to execute

        Returns:
            Result value (type depends on RPC)

        Raises:
            Exception: If RPC not found or execution fails
        """
        # Look up RPC definition to find M routine
        rpc_name = rpc_call.rpc_name

        # Find RPC in ^XWB(8994)
        b_index = yottadb.Key("^XWB")["8994"]["B"][rpc_name]
        try:
            rpc_ien = next(b_index.subscripts)
        except StopIteration:
            raise Exception("RPC {} not found".format(rpc_name))

        # Get RPC definition
        rpc_key = yottadb.Key("^XWB")["8994"][rpc_ien]
        zeroth = rpc_key["0"].value.decode("utf-8")
        pieces = zeroth.split("^")

        tag = pieces[1] if len(pieces) > 1 else ""
        routine = pieces[2] if len(pieces) > 2 else ""

        if not tag or not routine:
            raise Exception("RPC {} has no entry point".format(rpc_name))

        # For simulation, we can't easily call M routines with parameters
        # So we'll return a simulated result based on common RPC patterns

        # NOTE: In real implementation, you'd use yottadb.cip() to call M
        # But that requires complex setup. For now, return simulated data.

        return self._get_simulated_rpc_result(rpc_call, tag, routine)

    def _get_simulated_rpc_result(self, rpc_call, tag, routine):
        # type: (RPCCall, str, str) -> Any
        """
        Generate simulated RPC results for educational purposes.

        In real implementation, this would call the actual M routine.
        """
        rpc_name = rpc_call.rpc_name

        # Simulate common patient RPCs
        if "ORWPT" in rpc_name:
            return self._simulate_patient_rpc(rpc_call)
        elif "XUS" in rpc_name:
            return self._simulate_auth_rpc(rpc_call)
        else:
            return {"simulated": True, "rpc": rpc_name, "note": "Simulation only"}

    def _simulate_patient_rpc(self, rpc_call):
        # type: (RPCCall) -> Any
        """Simulate patient-related RPC results."""
        rpc_name = rpc_call.rpc_name

        if rpc_name == "ORWPT SELECT":
            # Simulate patient search results
            search_term = rpc_call.params[0] if rpc_call.params else "SMITH"
            # Read actual patient data from ^DPT
            patients = []
            try:
                dpt = yottadb.Key("^DPT")
                count = 0
                for ien in dpt.subscripts:
                    try:
                        zeroth = dpt[ien]["0"].value.decode("utf-8")
                        name = zeroth.split("^")[0]
                        if search_term.upper() in name.upper():
                            patients.append("{}^{}".format(
                                ien.decode("utf-8") if isinstance(ien, bytes) else ien,
                                name
                            ))
                            count += 1
                            if count >= 10:
                                break
                    except:
                        pass
            except Exception as e:
                return ["Error: {}".format(str(e))]

            return patients if patients else ["No patients found"]

        elif rpc_name == "ORWPT ID INFO":
            # Simulate patient identifier info
            dfn = rpc_call.params[0] if rpc_call.params else "1"
            try:
                dpt = yottadb.Key("^DPT")[dfn]
                zeroth = dpt["0"].value.decode("utf-8")
                pieces = zeroth.split("^")
                name = pieces[0] if len(pieces) > 0 else ""
                sex = pieces[1] if len(pieces) > 1 else ""
                dob = pieces[2] if len(pieces) > 2 else ""
                ssn = pieces[8] if len(pieces) > 8 else ""

                return "{}^{}^{}^{}".format(dfn, ssn, dob, sex)
            except:
                return "Error: Patient not found"

        else:
            return {"simulated": True, "rpc": rpc_name}

    def _simulate_auth_rpc(self, rpc_call):
        # type: (RPCCall) -> Any
        """Simulate authentication RPC results."""
        return {"simulated": True, "rpc": rpc_call.rpc_name, "note": "Auth simulation"}

    def disconnect_all_sites(self):
        # type: () -> None
        """Disconnect from all sites."""
        for site in self.sites.values():
            site.disconnect()


def demo():
    # type: () -> None
    """
    Demonstration of VistaDataService pattern.

    Shows how JLV would:
    1. Register VistA sites
    2. Connect to sites
    3. Execute RPCs
    4. Handle results
    """
    print("=" * 60)
    print("VistA Data Service Demonstration")
    print("Simulating JLV's VistaDataService component")
    print("=" * 60)

    # Create data service
    service = VistaDataService()

    # Register a VistA site (in real JLV, would register multiple sites)
    vehu_site = VistaSite(
        site_code="500",
        name="VEHU Development",
        description="WorldVistA VEHU test environment"
    )
    service.register_site(vehu_site)

    print("\n1. Registered Sites:")
    for site_code, site in service.sites.items():
        print("   - {}".format(site))

    # Connect to all sites
    print("\n2. Connecting to sites...")
    connections = service.connect_all_sites()
    for site_code, connected in connections.items():
        status = "SUCCESS" if connected else "FAILED"
        print("   - Site {}: {}".format(site_code, status))

    # Execute a single RPC on specific site
    print("\n3. Executing RPC: ORWPT SELECT")
    rpc_call = RPCCall("ORWPT SELECT", ["SMITH"])
    result = service.execute_rpc("500", rpc_call)

    print("   Result: {}".format(result))
    if result.success:
        print("   Patients found:")
        for patient in result.value:
            print("      - {}".format(patient))

    # Execute RPC on all sites (in real JLV, would query multiple VistA sites)
    print("\n4. Executing RPC on ALL sites:")
    all_results = service.execute_rpc_all_sites(rpc_call)
    for site_code, site_result in all_results.items():
        print("   Site {}: {}".format(site_code, site_result))

    # Disconnect
    print("\n5. Disconnecting from sites...")
    service.disconnect_all_sites()
    print("   All sites disconnected")

    print("\n" + "=" * 60)
    print("Demonstration complete")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print("Error: {}".format(e), file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
