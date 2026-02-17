# ---------------------------------------------------------------------------------
# cli/10_jlv_patient_aggregator.py
# ---------------------------------------------------------------------------------
# Patient Data Aggregator - demonstrates JLV's multi-RPC data aggregation pattern

# This script shows how JLV aggregates patient data by calling multiple RPCs
# across different clinical domains:
# - Demographics (ORWPT* RPCs)
# - Medications (ORWPS* RPCs)
# - Laboratory (ORQQAL* RPCs)
# - Vitals (ORQQVI* RPCs)
# - Problem List, Allergies, etc.

# In production JLV:
# - Calls these RPCs on MULTIPLE VistA sites
# - Aggregates results into a unified patient view
# - Handles data conflicts and versioning
# - Provides caching and performance optimization

# This simulation:
# - Calls RPCs on single VEHU instance
# - Demonstrates the aggregation pattern
# - Shows error handling
# - Educational purposes only
# ---------------------------------------------------------------------------------

"""
To run:
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/patient_aggregator.py --patient-id 1'

Examples:
  # Aggregate data for patient IEN 1
  docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --patient-id 1'

  # Search for patient first, then aggregate
  docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --search SMITH'

  # Verbose output showing all RPC calls
  docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --patient-id 1 --verbose'
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import yottadb
from yottadb import YDBError

# Import our VistaDataService simulation
from vista_data_service import VistaDataService, VistaSite, RPCCall, RPCResult


class PatientRecord:
    """
    Unified patient record aggregated from multiple RPCs.

    This simulates JLV's patient data model which combines:
    - Demographics
    - Clinical data (meds, labs, vitals)
    - Administrative data
    - Data from multiple VistA sites
    """

    def __init__(self, dfn, site_code):
        # type: (str, str) -> None
        """
        Initialize patient record.

        Args:
            dfn: Patient IEN/DFN
            site_code: VistA site this data came from
        """
        self.dfn = dfn
        self.site_code = site_code
        self.demographics = {}  # type: Dict[str, Any]
        self.identifiers = {}  # type: Dict[str, str]
        self.medications = []  # type: List[Dict[str, Any]]
        self.vitals = []  # type: List[Dict[str, Any]]
        self.labs = []  # type: List[Dict[str, Any]]
        self.allergies = []  # type: List[str]
        self.problems = []  # type: List[str]
        self.errors = []  # type: List[str]

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """Convert to dictionary for JSON serialization."""
        return {
            "dfn": self.dfn,
            "site": self.site_code,
            "demographics": self.demographics,
            "identifiers": self.identifiers,
            "medications": self.medications,
            "vitals": self.vitals,
            "labs": self.labs,
            "allergies": self.allergies,
            "problems": self.problems,
            "errors": self.errors
        }


class PatientAggregator:
    """
    Aggregates patient data by calling multiple RPCs.

    This simulates JLV's data aggregation logic which:
    1. Queries multiple RPCs for different data domains
    2. Combines results into unified patient view
    3. Handles errors gracefully
    4. Caches results for performance
    """

    def __init__(self, data_service, verbose=False):
        # type: (VistaDataService, bool) -> None
        """
        Initialize aggregator.

        Args:
            data_service: VistaDataService instance
            verbose: Whether to print detailed progress
        """
        self.data_service = data_service
        self.verbose = verbose

    def _log(self, message):
        # type: (str) -> None
        """Log message if verbose mode enabled."""
        if self.verbose:
            print("[Aggregator] {}".format(message))

    def aggregate_patient_data(self, dfn, site_code):
        # type: (str, str) -> PatientRecord
        """
        Aggregate complete patient data from multiple RPCs.

        This demonstrates JLV's pattern of calling multiple RPCs
        to build a comprehensive patient view.

        Args:
            dfn: Patient IEN/DFN
            site_code: Which site to query

        Returns:
            PatientRecord with aggregated data
        """
        record = PatientRecord(dfn, site_code)

        # 1. Get demographics (foundational)
        self._log("Fetching demographics for patient {}...".format(dfn))
        self._aggregate_demographics(record, site_code)

        # 2. Get identifiers (SSN, ICN, etc.)
        self._log("Fetching identifiers...")
        self._aggregate_identifiers(record, site_code)

        # 3. Get clinical data (medications, labs, vitals)
        self._log("Fetching medications...")
        self._aggregate_medications(record, site_code)

        self._log("Fetching vitals...")
        self._aggregate_vitals(record, site_code)

        # 4. Get allergies and problems
        self._log("Fetching allergies...")
        self._aggregate_allergies(record, site_code)

        self._log("Fetching problems...")
        self._aggregate_problems(record, site_code)

        self._log("Aggregation complete")
        return record

    def _aggregate_demographics(self, record, site_code):
        # type: (PatientRecord, str) -> None
        """Fetch patient demographics from ^DPT global."""
        try:
            dpt = yottadb.Key("^DPT")[record.dfn]
            zeroth = dpt["0"].value.decode("utf-8")
            pieces = zeroth.split("^")

            record.demographics = {
                "name": pieces[0] if len(pieces) > 0 else "",
                "sex": pieces[1] if len(pieces) > 1 else "",
                "dob": pieces[2] if len(pieces) > 2 else "",
                "age": self._calculate_age_from_fileman(pieces[2]) if len(pieces) > 2 else None,
            }
        except Exception as e:
            record.errors.append("Demographics: {}".format(str(e)))

    def _aggregate_identifiers(self, record, site_code):
        # type: (PatientRecord, str) -> None
        """Fetch patient identifiers (SSN, ICN)."""
        try:
            dpt = yottadb.Key("^DPT")[record.dfn]
            zeroth = dpt["0"].value.decode("utf-8")
            pieces = zeroth.split("^")

            # SSN from piece 9 (0-indexed piece 8)
            record.identifiers["ssn"] = pieces[8] if len(pieces) > 8 else ""

            # ICN from separate subscript
            try:
                icn = dpt["ICN"].value.decode("utf-8")
                record.identifiers["icn"] = icn
            except:
                record.identifiers["icn"] = ""

            record.identifiers["dfn"] = record.dfn
            record.identifiers["site"] = site_code

        except Exception as e:
            record.errors.append("Identifiers: {}".format(str(e)))

    def _aggregate_medications(self, record, site_code):
        # type: (PatientRecord, str) -> None
        """
        Fetch active medications.

        In real JLV: Would call ORWPS ACTIVE RPC
        In simulation: Read from prescription global or return placeholder
        """
        try:
            # In VEHU, medications are in ^PS global (Pharmacy)
            # For simulation, return placeholder
            record.medications = [
                {"name": "Simulated Medication 1", "status": "active", "source": "simulation"},
                {"name": "Simulated Medication 2", "status": "active", "source": "simulation"}
            ]
        except Exception as e:
            record.errors.append("Medications: {}".format(str(e)))

    def _aggregate_vitals(self, record, site_code):
        # type: (PatientRecord, str) -> None
        """
        Fetch vital signs.

        In real JLV: Would call ORQQVI VITALS RPC
        In simulation: Read from vitals global or return placeholder
        """
        try:
            # Vitals are in ^GMR global (Medicine Package)
            # For simulation, return placeholder
            record.vitals = [
                {"type": "Blood Pressure", "value": "120/80", "date": "recent", "source": "simulation"},
                {"type": "Temperature", "value": "98.6", "date": "recent", "source": "simulation"}
            ]
        except Exception as e:
            record.errors.append("Vitals: {}".format(str(e)))

    def _aggregate_allergies(self, record, site_code):
        # type: (PatientRecord, str) -> None
        """
        Fetch allergies.

        In real JLV: Would call allergy RPC
        In simulation: Check allergy subscript or return placeholder
        """
        try:
            # Allergies might be in ^DPT(dfn,"AL") or ^GMRD
            dpt = yottadb.Key("^DPT")[record.dfn]
            try:
                # Try to read allergy data
                for sub in dpt["AL"].subscripts:
                    allergy_data = dpt["AL"][sub]["0"].value.decode("utf-8")
                    record.allergies.append(allergy_data)
            except:
                record.allergies = ["(No allergies recorded or unable to read)"]
        except Exception as e:
            record.errors.append("Allergies: {}".format(str(e)))

    def _aggregate_problems(self, record, site_code):
        # type: (PatientRecord, str) -> None
        """
        Fetch problem list.

        In real JLV: Would call problem list RPC
        In simulation: Return placeholder
        """
        try:
            record.problems = [
                "Simulated Problem 1",
                "Simulated Problem 2"
            ]
        except Exception as e:
            record.errors.append("Problems: {}".format(str(e)))

    def _calculate_age_from_fileman(self, fileman_date):
        # type: (str) -> Optional[int]
        """
        Calculate age from FileMan date format.

        FileMan date: YYYMMDD where YYY is years since 1700
        Example: 2450101 = January 1, 1945

        Args:
            fileman_date: Date in FileMan format

        Returns:
            Age in years, or None if unable to calculate
        """
        if not fileman_date or len(fileman_date) < 7:
            return None

        try:
            year_since_1700 = int(fileman_date[:3])
            birth_year = 1700 + year_since_1700

            # Rough age calculation (current year - birth year)
            # In FileMan format, year 326 = 2026
            current_year = 2026  # Hardcoded for simulation
            age = current_year - birth_year

            return age if age >= 0 else None
        except:
            return None

    def search_patients(self, search_term, site_code):
        # type: (str, str) -> List[Dict[str, str]]
        """
        Search for patients by name.

        Args:
            search_term: Name or identifier to search
            site_code: Which site to search

        Returns:
            List of matching patients
        """
        self._log("Searching for patients matching: {}".format(search_term))

        rpc_call = RPCCall("ORWPT SELECT", [search_term])
        result = self.data_service.execute_rpc(site_code, rpc_call)

        patients = []
        if result.success and isinstance(result.value, list):
            for line in result.value:
                if "^" in line:
                    parts = line.split("^")
                    patients.append({
                        "dfn": parts[0],
                        "name": parts[1] if len(parts) > 1 else "",
                        "site": site_code
                    })

        return patients


def print_patient_record(record):
    # type: (PatientRecord) -> None
    """Print patient record in human-readable format."""
    print("\n" + "=" * 60)
    print("PATIENT RECORD - Site {}".format(record.site_code))
    print("=" * 60)

    # Demographics
    print("\nDEMOGRAPHICS:")
    print("  Name:     {}".format(record.demographics.get("name", "(unknown)")))
    print("  Sex:      {}".format(record.demographics.get("sex", "(unknown)")))
    print("  DOB:      {}".format(record.demographics.get("dob", "(unknown)")))
    print("  Age:      {}".format(record.demographics.get("age", "(unknown)")))

    # Identifiers
    print("\nIDENTIFIERS:")
    print("  DFN:      {}".format(record.identifiers.get("dfn", "")))
    print("  SSN:      {}".format(record.identifiers.get("ssn", "(not recorded)")))
    print("  ICN:      {}".format(record.identifiers.get("icn", "(not recorded)")))

    # Medications
    print("\nMEDICATIONS ({})".format(len(record.medications)))
    if record.medications:
        for med in record.medications:
            print("  - {}".format(med.get("name", "Unknown")))
    else:
        print("  (none)")

    # Vitals
    print("\nVITAL SIGNS ({})".format(len(record.vitals)))
    if record.vitals:
        for vital in record.vitals:
            print("  - {}: {}".format(vital.get("type", "Unknown"), vital.get("value", "")))
    else:
        print("  (none)")

    # Allergies
    print("\nALLERGIES ({})".format(len(record.allergies)))
    if record.allergies:
        for allergy in record.allergies:
            print("  - {}".format(allergy))
    else:
        print("  (none)")

    # Problems
    print("\nPROBLEMS ({})".format(len(record.problems)))
    if record.problems:
        for problem in record.problems:
            print("  - {}".format(problem))
    else:
        print("  (none)")

    # Errors
    if record.errors:
        print("\nERRORS:")
        for error in record.errors:
            print("  ! {}".format(error))

    print("\n" + "=" * 60)


def main():
    # type: () -> None
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Aggregate patient data from multiple RPCs (JLV pattern)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aggregate data for patient IEN 1
  %(prog)s --patient-id 1

  # Search for patient first
  %(prog)s --search SMITH

  # Verbose mode
  %(prog)s --patient-id 1 --verbose

  # Output as JSON
  %(prog)s --patient-id 1 --json
        """
    )

    parser.add_argument(
        "--patient-id",
        type=str,
        help="Patient DFN/IEN to aggregate data for"
    )

    parser.add_argument(
        "--search",
        type=str,
        help="Search for patients by name"
    )

    parser.add_argument(
        "--site",
        type=str,
        default="500",
        help="VistA site code (default: 500)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output showing RPC calls"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.patient_id and not args.search:
        parser.error("Must specify either --patient-id or --search")

    # Initialize data service
    service = VistaDataService()
    vehu_site = VistaSite(args.site, "VEHU Development")
    service.register_site(vehu_site)

    if args.verbose:
        print("Connecting to VistA site {}...".format(args.site))

    connections = service.connect_all_sites()
    if not connections.get(args.site):
        print("Error: Unable to connect to site {}".format(args.site), file=sys.stderr)
        sys.exit(1)

    # Create aggregator
    aggregator = PatientAggregator(service, verbose=args.verbose)

    # Search mode
    if args.search:
        print("Searching for patients matching: {}".format(args.search))
        patients = aggregator.search_patients(args.search, args.site)

        if not patients:
            print("No patients found")
            sys.exit(0)

        print("\nFound {} patient(s):".format(len(patients)))
        for idx, patient in enumerate(patients, 1):
            print("  {}. {} (DFN: {})".format(idx, patient["name"], patient["dfn"]))

        # If only one patient, aggregate their data
        if len(patients) == 1:
            patient_id = patients[0]["dfn"]
            print("\nAggregating data for patient DFN {}...".format(patient_id))
            record = aggregator.aggregate_patient_data(patient_id, args.site)

            if args.json:
                print(json.dumps(record.to_dict(), indent=2))
            else:
                print_patient_record(record)

        sys.exit(0)

    # Direct patient ID mode
    if args.patient_id:
        if args.verbose:
            print("Aggregating data for patient DFN {}...".format(args.patient_id))

        record = aggregator.aggregate_patient_data(args.patient_id, args.site)

        if args.json:
            print(json.dumps(record.to_dict(), indent=2))
        else:
            print_patient_record(record)

    service.disconnect_all_sites()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print("Error: {}".format(e), file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
