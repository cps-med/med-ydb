# Joint Longitudinal Viewer (JLV) and RPC Integration Patterns

**Goal**: Understand how JLV aggregates patient data from multiple VistA sites using RPCs

**Prerequisites**:
- Read `06-vista-rpc-broker.md` (RPC fundamentals)
- Run `app/04_rpc_explorer.py` (explore RPC definitions)

---

## Overview: What is JLV?

**Joint Longitudinal Viewer (JLV)** is a VA/DoD system that provides a **unified view of patient data** across:
- Multiple VistA sites (VA facilities)
- DoD AHLTA/MHS GENESIS systems
- Community care providers

### The Core Challenge

A veteran may receive care at multiple VA facilities:
- San Francisco VA (Station 500)
- Palo Alto VA (Station 640)
- Portland VA (Station 648)

Each facility has its own VistA instance with its own patient records. **How do you view the complete patient history?**

**JLV's answer**: Query all sites and aggregate the results.

---

## JLV Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     JLV Web UI                          │
│              (Java/JavaScript frontend)                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              JLV Application Server                     │
│                                                         │
│   ┌────────────────────────────────────────────────┐    │
│   │         VistaDataService Component             │    │
│   │  - Manages connections to VistA sites          │    │
│   │  - Executes RPCs via RPC Broker protocol       │    │
│   │  - Aggregates results from multiple sites      │    │
│   └────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │ VistA   │ │ VistA   │ │ VistA   │
     │ Site A  │ │ Site B  │ │ Site C  │
     │(SF VA)  │ │(PA VA)  │ │(Port VA)│
     └─────────┘ └─────────┘ └─────────┘
          │           │           │
          └───────────┴───────────┘
               RPC Broker
            (TCP port 9430)
```

---

## How JLV Uses RPCs

### 1. Site Registration

JLV maintains a registry of VistA sites the veteran has records at:

```java
// Pseudocode - JLV pattern
List<VistaSite> sites = patientSiteRegistry.getSitesForPatient(icn);

// Each site has:
// - Station number (e.g., "500")
// - Hostname/IP
// - Port (9430)
// - Connection pool
```

### 2. Parallel RPC Execution

For each data request, JLV queries **all relevant sites** in parallel:

```java
// Pseudocode - JLV pattern
ExecutorService executor = Executors.newFixedThreadPool(sites.size());

List<Future<Demographics>> futures = new ArrayList<>();
for (VistaSite site : sites) {
    Future<Demographics> future = executor.submit(() -> {
        RPCBroker broker = connectionPool.getConnection(site);
        return broker.executeRPC("ORWPT ID INFO", patientDFN);
    });
    futures.add(future);
}

// Wait for all sites to respond (with timeout)
List<Demographics> allDemographics = new ArrayList<>();
for (Future<Demographics> future : futures) {
    try {
        Demographics demo = future.get(5, TimeUnit.SECONDS);
        allDemographics.add(demo);
    } catch (TimeoutException e) {
        // Site timed out, continue with others
    }
}
```

### 3. Data Aggregation and Deduplication

JLV combines results from multiple sites:

```java
// Pseudocode - JLV aggregation
PatientRecord unifiedRecord = new PatientRecord();

// Aggregate demographics (same patient, different sites)
unifiedRecord.setDemographics(mergeDemographics(allDemographics));

// Aggregate medications from all sites
List<Medication> allMeds = new ArrayList<>();
for (VistaSite site : sites) {
    List<Medication> siteMeds = queryMedications(site, patientDFN);
    allMeds.addAll(siteMeds);
}

// Sort by date, deduplicate, flag conflicts
unifiedRecord.setMedications(deduplicateAndSort(allMeds));
```

### 4. Common RPCs JLV Uses

| Domain | RPC | Purpose |
|--------|-----|---------|
| **Patient Lookup** | ORWPT SELECT | Find patient by name/SSN |
| **Demographics** | ORWPT ID INFO | Get identifiers (SSN, ICN, DOB) |
| **Medications** | ORWPS ACTIVE | Active medications |
| **Lab Results** | ORQQAL LIST | Laboratory results |
| **Vitals** | ORQQVI VITALS | Vital signs |
| **Radiology** | ORWRA REPORT TEXT | Radiology reports |
| **Allergies** | ORQQAL ALLERGY | Allergy list |
| **Problems** | ORQQPL PROBLEM LIST | Problem/diagnosis list |
| **Documents** | TIU GET RECORD TEXT | Clinical notes, discharge summaries |

---

## Your Simulation Scripts

You've created two scripts that demonstrate JLV's patterns:

### 1. `app/vista_data_service.py`

**Purpose**: Simulates JLV's VistaDataService component

**Key patterns demonstrated**:
- `VistaSite` class: Represents a VistA station
- `RPCCall` class: Encapsulates RPC requests
- `RPCResult` class: Encapsulates RPC responses
- `VistaDataService` class: Coordinates RPC execution

**Usage**:
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/vista_data_service.py'
```

**What it shows**:
- Site registration pattern
- Connection management
- RPC execution on specific site
- RPC execution across all sites (multi-site pattern)

### 2. `app/patient_aggregator.py`

**Purpose**: Demonstrates multi-RPC data aggregation (like JLV does for patient records)

**Key patterns demonstrated**:
- `PatientRecord` class: Unified patient data model
- `PatientAggregator` class: Calls multiple RPCs and combines results
- Error handling when RPCs fail
- Building comprehensive patient view from disparate data sources

**Usage**:
```bash
# Search for patient
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --search SMITH'

# Aggregate data for specific patient
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --patient-id 1 --verbose'

# JSON output
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --patient-id 1 --json'
```

**What it shows**:
- Calling multiple RPCs for different data domains
- Aggregating results into unified record
- Error handling per domain
- Verbose logging of RPC calls

---

## Differences: Real JLV vs. Your Simulation

| Aspect | Real JLV | Your Simulation |
|--------|----------|-----------------|
| **Language** | Java | Python |
| **Sites** | Multiple VistA instances | Single VEHU instance |
| **RPC Protocol** | RPC Broker over TCP (port 9430) | Direct M routine calls via YottaDB |
| **Authentication** | Access/Verify codes per site | No authentication (local access) |
| **Parallelism** | True parallel execution across sites | Sequential (single site) |
| **Caching** | Redis/Memcached | No caching |
| **Error Handling** | Sophisticated retry logic, circuit breakers | Basic try/except |
| **Patient Matching** | ICN-based cross-site matching | Single-site DFN only |

**Your simulation captures the essence of JLV's patterns** for educational purposes!

---

## Key JLV Concepts

### 1. Integration Control Number (ICN)

**Problem**: Each VistA site has its own patient IEN/DFN. How do you know patient DFN=123 at Site A is the same person as DFN=456 at Site B?

**Solution**: **ICN** - a national identifier assigned by MPI (Master Patient Index)

```
Patient John Smith:
- San Francisco VA (500):  DFN = 123,  ICN = 1000000123V456
- Palo Alto VA (640):      DFN = 456,  ICN = 1000000123V456  ← Same ICN!
- Portland VA (648):       DFN = 789,  ICN = 1000000123V456
```

JLV uses ICN to find the patient's local DFN at each site.

### 2. Data Freshness and Caching

**Challenge**: Querying 10+ VistA sites for every page load is slow

**JLV's strategy**:
- Cache demographics (rarely change)
- Fresh query for clinical data (meds, labs, vitals)
- Background refresh of older data
- Time-to-live (TTL) per data type

### 3. Conflict Resolution

**Scenario**: Patient demographics differ across sites

```
Site A: Name = "SMITH, JOHN Q"
Site B: Name = "SMITH, JOHN"
Site C: Name = "SMITH, JOHN QUINCY"
```

**JLV's approach**:
- Use "most complete" record (longest name)
- Flag conflicts for clinical staff review
- Display data source (which site) for each data element

### 4. Timeout and Degraded Mode

**Challenge**: Site B is down or slow

**JLV's approach**:
- Set timeout per site (e.g., 5 seconds)
- If site times out, show data from other sites
- Display warning: "Data from Site B unavailable"
- Don't block entire UI for one slow site

---

## Hands-On Exercises

### Exercise 1: Run the Simulation Scripts

```bash
# 1. Test VistaDataService
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/vista_data_service.py'

# 2. Search for a patient
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --search SMITH'

# 3. Aggregate data for a patient (verbose mode)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/patient_aggregator.py --patient-id 1 --verbose'
```

**Questions**:
1. What RPCs are called during aggregation?
2. How does the aggregator handle missing data?
3. What errors are caught and logged?

### Exercise 2: Enhance the Aggregator

Modify `patient_aggregator.py` to add a new data domain:

**Task**: Add immunization history aggregation

```python
def _aggregate_immunizations(self, record, site_code):
    # type: (PatientRecord, str) -> None
    """
    Fetch immunization history.

    In real JLV: Would call immunization RPC
    Hint: Immunizations are in ^AUPNVIMM or ^PXRMINDX globals
    """
    try:
        # Your code here: Read from immunization globals
        record.immunizations = []
    except Exception as e:
        record.errors.append("Immunizations: {}".format(str(e)))
```

### Exercise 3: Multi-Site Simulation

Enhance `vista_data_service.py` to simulate multiple sites:

**Task**: Register 3 "virtual" sites (same VEHU, but pretend they're different)

```python
# Register multiple sites
service.register_site(VistaSite("500", "San Francisco VA"))
service.register_site(VistaSite("640", "Palo Alto VA"))
service.register_site(VistaSite("648", "Portland VA"))

# Execute RPC on all sites
results = service.execute_rpc_all_sites(rpc_call)

# Show results from each "site"
for site_code, result in results.items():
    print("Site {}: {}".format(site_code, result))
```

---

## Production Considerations

If you were building a real JLV-like system:

### 1. Authentication Per Site

```python
class VistaSite:
    def __init__(self, site_code, host, port, credentials):
        self.site_code = site_code
        self.host = host
        self.port = port
        self.access_code = credentials["access"]
        self.verify_code = credentials["verify"]

    def connect(self):
        # Real RPC Broker authentication
        self.broker = RPCBroker(self.host, self.port)
        self.broker.connect()
        self.broker.login(self.access_code, self.verify_code)
        self.broker.set_context("OR CPRS GUI CHART")
```

### 2. Connection Pooling

```python
class ConnectionPool:
    def __init__(self, site, pool_size=5):
        self.site = site
        self.pool = Queue(maxsize=pool_size)

        # Pre-create connections
        for _ in range(pool_size):
            broker = self._create_connection()
            self.pool.put(broker)

    def get_connection(self, timeout=5):
        return self.pool.get(timeout=timeout)

    def release_connection(self, broker):
        self.pool.put(broker)
```

### 3. Async/Parallel Execution

```python
import asyncio

async def query_all_sites(sites, rpc_call):
    tasks = []
    for site in sites:
        task = asyncio.create_task(execute_rpc_async(site, rpc_call))
        tasks.append(task)

    # Gather results with timeout
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 4. Caching Layer

```python
import redis

class CachedVistaDataService:
    def __init__(self, data_service, redis_client):
        self.data_service = data_service
        self.cache = redis_client

    def get_patient_demographics(self, dfn, site_code):
        # Check cache first
        cache_key = "demo:{}:{}".format(site_code, dfn)
        cached = self.cache.get(cache_key)

        if cached:
            return json.loads(cached)

        # Cache miss - query VistA
        result = self.data_service.execute_rpc(
            site_code,
            RPCCall("ORWPT ID INFO", [dfn])
        )

        # Cache for 1 hour
        self.cache.setex(cache_key, 3600, json.dumps(result.value))

        return result.value
```

---

## Key Takeaways

1. **JLV aggregates data from multiple VistA sites** using RPCs
2. **VistaDataService pattern**: Separate concerns (connection, execution, aggregation)
3. **ICN is critical** for cross-site patient matching
4. **Parallel execution** is essential for acceptable performance
5. **Graceful degradation**: System works even if some sites are unavailable
6. **Your simulation captures the core patterns** for learning purposes

---

## Next Steps

**Right Now**:
1. Run `vista_data_service.py` to see the site management pattern
2. Run `patient_aggregator.py` to see multi-RPC aggregation
3. Complete Exercise 1: Understand the RPC call flow

**This Week**:
- Complete Exercise 2: Add immunization aggregation
- Explore actual RPC definitions for the RPCs mentioned (use `04_rpc_explorer.py`)
- Research MPI and ICN assignment in VistA

**Future** (Building Modern UI):
- Design FastAPI endpoints that wrap these aggregation patterns
- Implement caching layer (Redis)
- Add authentication and authorization
- Build React/HTMX frontend consuming aggregated data

---

## References

### JLV Documentation
- VistA Expertise Network: JLV architecture discussions
- OSEHRA: JLV open source components (if available)

### Related VistA Systems
- **MPI (Master Patient Index)**: Assigns and manages ICN
- **HDR (Health Data Repository)**: Alternative to JLV for some data
- **VIA (Veterans Information Architecture)**: Newer data integration approach

### Your Scripts
- `app/vista_data_service.py` - VistaDataService simulation
- `app/patient_aggregator.py` - Multi-RPC aggregation demo
- `app/04_rpc_explorer.py` - Explore RPC definitions

---

## Appendix: JLV RPC Usage Patterns

Common patterns you'll see in JLV-style code:

### Pattern 1: Try All Sites, Accept Partial Results

```python
results = {}
for site in sites:
    try:
        result = execute_rpc(site, rpc_call)
        results[site.code] = result
    except TimeoutException:
        results[site.code] = None  # Site unavailable

# Continue with whatever results we got
return aggregate_partial_results(results)
```

### Pattern 2: Primary Site + Fallback Sites

```python
# Try patient's primary site first
primary_result = execute_rpc(primary_site, rpc_call)

if primary_result.success:
    return primary_result

# Primary failed, try other sites
for fallback_site in other_sites:
    result = execute_rpc(fallback_site, rpc_call)
    if result.success:
        return result
```

### Pattern 3: Aggregate Then Deduplicate

```python
all_medications = []

for site in sites:
    site_meds = query_medications(site, patient_id)
    all_medications.extend(site_meds)

# Deduplicate by medication name + start date
unique_meds = deduplicate(all_medications, key=lambda m: (m.name, m.start_date))

# Sort by most recent first
return sorted(unique_meds, key=lambda m: m.start_date, reverse=True)
```

These patterns help build robust multi-site systems!
