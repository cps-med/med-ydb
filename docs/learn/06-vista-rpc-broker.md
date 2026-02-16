# VistA Remote Procedure Call (RPC) Interface

**Goal**: Understand how client applications like CPRS communicate with VistA through the RPC Broker protocol

**Prerequisites**:
- Read `02-fileman-architecture.md` (FileMan structure)
- Read `03-m-language-primer.md` (M routines and functions)
- Read `04-vista-patient-data.md` (example VistA data)

---

## Overview: VistA's Application Programming Interface

### What Are RPCs?

**Remote Procedure Calls (RPCs)** are VistA's application programming interface (API). They allow client applications to:
- Query patient data
- Place orders (medications, labs, radiology)
- Update records
- Access VistA business logic

**Think of RPCs as VistA's REST API** - but designed in the 1990s for terminal-based and Windows client applications.

### Why RPCs Exist

VistA was designed as a client-server system:

```
┌─────────────────┐         RPC Broker           ┌─────────────────┐
│  CPRS (Windows) │◄─────────Protocol───────────►│  VistA Server   │
│  GUI Client     │         TCP/IP 9430          │  (VEHU)         │
└─────────────────┘                              └─────────────────┘
                                                          │
                                                   Calls M Routines
                                                          │
                                                          ▼
                                                  ┌──────────────┐
                                                  │  ^DPT, ^OR,  │
                                                  │  ^LAB, etc.  │
                                                  └──────────────┘
```

**Key benefits**:
1. **Abstraction**: Clients don't access globals directly
2. **Business logic**: RPCs enforce VistA's rules (validation, security, workflow)
3. **Security**: Authentication and authorization built-in
4. **Versioning**: RPC definitions can evolve without breaking clients

### RPC vs. Direct Global Access

| Approach | Use Case | Safety | Complexity |
|----------|----------|--------|------------|
| **Direct Global Access** | Learning, data exploration, reporting | Low (can bypass validation) | Simple (but dangerous) |
| **RPC Calls** | Production applications, CPRS | High (business logic enforced) | Moderate (protocol overhead) |

**Your learning scripts** use direct global access for read-only exploration. **Production applications** like CPRS use RPCs exclusively.

---

## The RPC Broker Protocol

### Protocol Overview

The **RPC Broker** is VistA's protocol for remote procedure calls over TCP/IP.

**Protocol characteristics**:
- **Binary protocol** with custom framing (not HTTP)
- **Stateful**: Maintains connection context (user, menu option)
- **Port**: Default 9430 (configurable)
- **Authentication**: VistA Access/Verify codes or SSO tokens

### Connection Lifecycle

```
1. CONNECT    → TCP connection to port 9430
2. HANDSHAKE  → Exchange protocol version
3. LOGIN      → Authenticate with Access/Verify codes
4. CONTEXT    → Set menu option context (authorization)
5. RPC CALLS  → Execute procedures (can be many)
6. DISCONNECT → Close connection
```

### Wire Protocol Format

RPC Broker uses a custom text-based protocol with length-prefixed strings:

**Example RPC call**:
```
[XWB]11302\x001.108\x00TCPConnect50007localhost.localdomain0123\x00
```

**Breakdown**:
- `[XWB]` - Protocol signature
- `11302` - Protocol version
- `\x00` - Field separator (NULL byte)
- `1.108` - Namespace version
- `TCPConnect` - Connection type
- `50007` - Client port
- `localhost.localdomain` - Client hostname
- `0123` - Client IP

**This is complex!** Fortunately, libraries exist to handle this protocol.

### Comparison to Modern APIs

| Feature | VistA RPC Broker | REST API | GraphQL |
|---------|-----------------|----------|---------|
| **Protocol** | Custom binary over TCP | HTTP/JSON | HTTP/JSON |
| **State** | Stateful (connection context) | Stateless | Stateless |
| **Authentication** | Per-connection | Per-request (token) | Per-request (token) |
| **Authorization** | Menu option context | Endpoint permissions | Resolver permissions |
| **Return format** | String, array, or global | JSON | JSON |
| **Versioning** | RPC name/version | URL version or header | Schema evolution |

**Key insight**: RPC Broker is more like gRPC or CORBA than REST. It's a **procedure-oriented** API, not resource-oriented.

---

## RPC Structure and Metadata

### RPC Definitions: File #8994

RPCs are defined in the **REMOTE PROCEDURE file** (File #8994), stored in global `^XWB(8994,`.

**Example RPC definition structure**:
```
^XWB(8994, RPC_IEN, 0) = "RPC_NAME^TAG^ROUTINE^..."
^XWB(8994, RPC_IEN, .1) = "DESCRIPTION TEXT"
^XWB(8994, RPC_IEN, 1) = "RETURN VALUE TYPE"
^XWB(8994, RPC_IEN, 2, n) = "PARAMETER n DEFINITION"
```

### Examining an RPC: ORWPT SELECT

**Purpose**: Search for patients by name or identifier

**Let's inspect this RPC's definition**:

```m
; In M direct mode or via Python
SET IEN=$ORDER(^XWB(8994,"B","ORWPT SELECT",""))
WRITE ^XWB(8994,IEN,0)
; Output: ORWPT SELECT^SELPT^ORWPT^0^...

; Parse this:
; - RPC Name: ORWPT SELECT
; - Entry point: TAG = SELPT, ROUTINE = ORWPT
; - So this RPC calls: DO SELPT^ORWPT
```

**In Python** (exploring the definition):
```python
import yottadb

# Find the RPC by name using the "B" index
rpc_name = "ORWPT SELECT"
rpc_file = yottadb.Key("^XWB")["8994"]

# The "B" index maps name → IEN
b_index = rpc_file["B"][rpc_name]
try:
    rpc_ien = next(b_index.subscripts)

    # Get the 0-node definition
    definition = rpc_file[rpc_ien][0].value.decode('utf-8')
    print(f"RPC Definition: {definition}")

    # Parse pieces
    pieces = definition.split("^")
    print(f"  Name: {pieces[0]}")
    print(f"  Tag: {pieces[1]}")
    print(f"  Routine: {pieces[2]}")
except StopIteration:
    print(f"RPC {rpc_name} not found")
```

### RPC Parameters

RPCs accept parameters in three forms:

#### 1. Literal Parameters
Simple string values passed by value.

**Example**: Patient identifier
```python
# Conceptual - actual broker protocol handles this
rpc_call("ORWPT SELECT", ["SMITH,JOHN"])
```

#### 2. Reference Parameters
Variables passed by reference (rare in modern RPCs).

#### 3. List/Array Parameters
Complex data structures passed as arrays.

**Example**: Search parameters
```python
# Parameter 1: Search string
# Parameter 2: Search flags (array)
rpc_call("ORWPT LIST ALL", ["SMITH", {"MAX": 44, "FROM": 1}])
```

### RPC Return Types

RPCs return data in three formats:

#### 1. Single Value (Scalar)
Returns a simple string.

**Example**: `XWB GET VARIABLE VALUE` returns the value of a M variable
```
Return: "JOHN DOE"
```

#### 2. Array (Multiple Lines)
Returns an array of strings (like a list).

**Example**: `ORWPT SELECT` returns list of matching patients
```
Return[0]: "1^SMITH,JOHN^000-00-0001^19450101"
Return[1]: "2^SMITH,JANE^000-00-0002^19500615"
...
```

#### 3. Global Array
Returns data as a global reference (rare, for large datasets).

---

## Calling RPCs from Python

You have two main approaches to call VistA RPCs from Python:

### Option 1: RPC Broker Protocol Client (Production Approach)

Use an existing RPC Broker client library.

**Available libraries**:
- **PyVistA**: Python RPC Broker client (https://github.com/OSEHR/PyVistA)
- **node-vista**: Node.js client (could use via subprocess)
- **Roll your own**: Implement the broker protocol (complex)

**Example using conceptual library**:
```python
from vista_rpc import RPCBroker

# Connect
broker = RPCBroker("localhost", 9430)
broker.connect()

# Authenticate
broker.login(access_code="XXX", verify_code="YYY")

# Set context (menu option for authorization)
broker.set_context("OR CPRS GUI CHART")

# Call RPC
result = broker.call_rpc("ORWPT SELECT", ["SMITH"])

# Result is array of patients
for patient_line in result:
    print(patient_line)

broker.disconnect()
```

**Challenges**:
- Requires VistA credentials
- Must understand menu option contexts
- Protocol complexity
- VEHU access/verify codes may be test accounts

### Option 2: Direct M Routine Calls via yottadb (Learning Approach)

Call the underlying M routines **directly** using YottaDB's Python interface.

**How it works**:
1. Find the RPC definition (which M routine it calls)
2. Call that M routine using `yottadb.cip()`
3. Parse the return value

**Example: Calling an RPC's underlying routine**:

```python
import yottadb

# Most RPCs are complex and require setup
# But some utility RPCs are simpler

# Example: Call a simple M extrinsic function
# (This is illustrative - actual RPC routines need proper setup)

# First, understand what the RPC does by reading its M code
# Then call the M function directly if possible
```

**Limitations**:
- Bypasses authentication (security concern for writes!)
- Bypasses business logic (validation not enforced)
- Context not set (some RPCs require menu option permissions)
- **Only safe for read-only exploration or testing**

### Option 3: M Direct Mode (Manual Testing)

Test RPCs interactively in M:

```bash
docker exec -it vehu-dev bash
su - vehu
mumps -direct
```

```m
GTM>; Set up context (user, division, etc.)
GTM>SET DUZ=1  ; User IEN
GTM>SET DUZ(0)="@"  ; Programmer access (testing only!)
GTM>
GTM>; Call an RPC routine directly
GTM>DO SELPT^ORWPT(.RESULT,"SMITH")
GTM>
GTM>; View results
GTM>ZWRITE RESULT
RESULT(0)=1
RESULT(1)="1^SMITH,JOHN^000-00-0001^19450101"
GTM>
```

**This is the easiest way to explore RPCs** during learning!

---

## Common VistA RPCs

### Patient RPCs (ORWPT* namespace)

#### ORWPT SELECT
**Purpose**: Search for patients by name or identifier

**Parameters**:
1. Search string (e.g., "SMITH", "000-00-0001", partial name)

**Returns**: Array of matching patients
```
IEN^NAME^SSN^DOB^SEX^...
```

**Example return**:
```
1^SMITH,JOHN DOE^000-00-0001^2450101^M
2^SMITH,JANE MARY^000-00-0002^2500615^F
```

#### ORWPT ID INFO
**Purpose**: Get patient identifiers (IEN, SSN, ICN, etc.)

**Parameters**:
1. Patient IEN (DFN)

**Returns**: Delimited string with identifiers
```
DFN^SSN^DOB^SEX^VETERAN?^SC%^WARD^...
```

#### ORWPT FULLSSN
**Purpose**: Get patient's full SSN (security check required)

**Parameters**:
1. Patient IEN

**Returns**: Full SSN string

---

### User/Authentication RPCs (XUS* namespace)

#### XUS SIGNON SETUP
**Purpose**: Initial handshake, get server info

**Parameters**: None

**Returns**: Array with server configuration

#### XUS AV CODE
**Purpose**: Authenticate with Access/Verify codes

**Parameters**:
1. Access code + ";" + Verify code (encrypted)

**Returns**: User IEN and additional user info

#### XUS GET USER INFO
**Purpose**: Get current user's information

**Parameters**: None

**Returns**: Array with user details (name, service/section, etc.)

---

### Order RPCs (ORWDX*, ORWOR* namespace)

#### ORWOR SHEETS
**Purpose**: Get list of order sheets for a patient

**Parameters**:
1. Patient IEN

**Returns**: Array of order sheets available

#### ORWDX WRLST
**Purpose**: Get patient's active orders

**Parameters**:
1. Patient IEN
2. Order filters (array)

**Returns**: Array of orders

**Note**: Write operations (placing orders) require extensive context and validation. Read-only order queries are safer for learning.

---

### Clinical Data RPCs

#### ORQQVI VITALS
**Purpose**: Get patient vital signs

**Parameters**:
1. Patient IEN
2. Date range

**Returns**: Array of vital signs readings

#### ORWPS ACTIVE
**Purpose**: Get patient's active medications

**Parameters**:
1. Patient IEN

**Returns**: Array of active medication orders

---

## Safety and Security Considerations

### Authentication Requirements

**Production**: RPCs require valid VistA Access/Verify codes
- These authenticate the **user** (provider, nurse, clerk, etc.)
- Different users have different permissions

**VEHU/Testing**: May have test accounts (check VistA documentation)
- Often: `fakedoc1` / `1doc!@#$` or similar test credentials
- **Never use production credentials in learning environments!**

### Context: Menu Option Authorization

RPCs require **context** - a menu option that grants authorization.

**Common contexts**:
- `OR CPRS GUI CHART` - CPRS clinician interface
- `OR CPRS GUI PHARMACY` - Pharmacy interface
- `XUPROG` - Programmer mode (testing only)

**Why context matters**:
```python
# Without context:
broker.call_rpc("ORWPT SELECT", ["SMITH"])
# → ERROR: Context not set

# With context:
broker.set_context("OR CPRS GUI CHART")
broker.call_rpc("ORWPT SELECT", ["SMITH"])
# → SUCCESS: Returns patient list
```

### Read vs. Write RPCs

| RPC Type | Examples | Risk Level | Learning Safety |
|----------|----------|------------|-----------------|
| **Read-only** | ORWPT SELECT, ORWPT ID INFO | Low | ✅ Safe to explore |
| **Write (non-destructive)** | ORWOR SHEETS (adds to workload) | Medium | ⚠️ Caution advised |
| **Write (patient data)** | Order entry, result verification | High | ❌ Avoid in learning |
| **Admin/Config** | User management, system config | Critical | ❌ Never in production |

### Testing in Safe Mode

**Best practices for learning**:

1. **Read-only RPCs first**: Focus on ORWPT*, XUS GET*, ORWPS ACTIVE (read-only)
2. **Test database**: Use VEHU (it's already a test environment)
3. **Document everything**: Keep notes on which RPCs you test
4. **Understand before calling**: Read the M routine code first
5. **Check RPC definition**: Verify return type and parameters

**Example safe exploration pattern**:
```python
# 1. Find RPC definition
# 2. Read its M routine source
# 3. Call it in M direct mode first (see what happens)
# 4. Then try via Python if needed
# 5. Document your findings
```

---

## Hands-On Exercises

### Exercise 1: Inspect RPC Definitions

**Goal**: Explore the REMOTE PROCEDURE file structure

```python
import yottadb

# List some RPCs related to patients
rpc_file = yottadb.Key("^XWB")["8994"]["B"]

print("Patient-related RPCs:")
count = 0
for rpc_name in rpc_file.subscripts:
    rpc_name_str = rpc_name.decode('utf-8') if isinstance(rpc_name, bytes) else rpc_name

    if rpc_name_str.startswith("ORWPT"):
        print(f"  - {rpc_name_str}")
        count += 1
        if count >= 10:
            break
```

**Questions**:
1. How many RPCs start with `ORWPT`?
2. What does the "B" index represent in FileMan?
3. Where is the actual M routine code stored?

---

### Exercise 2: Trace an RPC to Its M Routine

**Goal**: Find and read the M code behind an RPC

**Steps**:

1. **Find RPC definition**:
```python
import yottadb

rpc_name = "ORWPT SELECT"
b_index = yottadb.Key("^XWB")["8994"]["B"][rpc_name]
rpc_ien = next(b_index.subscripts)

definition = yottadb.Key("^XWB")["8994"][rpc_ien][0].value.decode('utf-8')
pieces = definition.split("^")

tag = pieces[1]      # e.g., "SELPT"
routine = pieces[2]  # e.g., "ORWPT"

print(f"RPC calls: DO {tag}^{routine}")
```

2. **Find the routine source**:
```bash
# In VEHU container
docker exec -it vehu-dev bash -lc "find /home/vehu -name 'ORWPT.m' 2>/dev/null"
```

3. **Read the routine**:
```bash
docker exec -it vehu-dev bash -lc "cat /path/to/ORWPT.m | grep -A 20 'SELPT'"
```

**Questions**:
1. What does the `SELPT` tag do?
2. What global does it query?
3. How does it format the return array?

---

### Exercise 3: Call a Simple RPC in M Direct Mode

**Goal**: Execute an RPC manually to see how it works

```bash
docker exec -it vehu-dev su - vehu -c 'mumps -direct' <<'EOF'
; Set up minimal user context
SET DUZ=1
SET DUZ(0)="@"
SET DT=$$DT^XLFDT()  ; Today's date in FileMan format

; Call patient selection RPC
NEW RESULT
DO SELPT^ORWPT(.RESULT,"SMITH")

; Display results
ZWRITE RESULT

HALT
EOF
```

**Expected output**:
```
RESULT(0)=2
RESULT(1)="1^SMITH,JOHN^000-00-0001^2450101"
RESULT(2)="2^SMITH,JANE^000-00-0002^2500615"
```

**Questions**:
1. What does `RESULT(0)` contain?
2. How are patient fields delimited in the results?
3. What happens if you search for a non-existent patient?

---

## Understanding RPC Return Formats

### Parsing Array Returns

Most patient/order RPCs return arrays. Each line is delimited with `^`.

**Example return from ORWPT SELECT**:
```
1^SMITH,JOHN^000-00-0001^2450101^M
```

**Parse in Python**:
```python
def parse_patient_search_result(line):
    """Parse a single patient line from ORWPT SELECT.

    Args:
        line: String like "IEN^NAME^SSN^DOB^SEX"

    Returns:
        dict with parsed fields
    """
    pieces = line.split("^")

    return {
        "ien": pieces[0] if len(pieces) > 0 else None,
        "name": pieces[1] if len(pieces) > 1 else None,
        "ssn": pieces[2] if len(pieces) > 2 else None,
        "dob": pieces[3] if len(pieces) > 3 else None,
        "sex": pieces[4] if len(pieces) > 4 else None,
    }

# Usage
result_line = "1^SMITH,JOHN^000-00-0001^2450101^M"
patient = parse_patient_search_result(result_line)
print(f"Patient: {patient['name']}, DOB: {patient['dob']}")
```

### Handling Multi-Line Returns

```python
# Conceptual RPC call result
rpc_result = [
    "1^SMITH,JOHN^000-00-0001^2450101^M",
    "2^SMITH,JANE^000-00-0002^2500615^F",
]

patients = [parse_patient_search_result(line) for line in rpc_result]

for patient in patients:
    print(f"{patient['ien']}: {patient['name']}")
```

---

## Bridge to Modern UI Development

### How FastAPI Could Wrap RPCs

**Vision**: Modern REST API wrapping VistA RPCs

```python
from fastapi import FastAPI, HTTPException
from vista_rpc import RPCBroker  # Hypothetical library

app = FastAPI()

@app.get("/api/patients/search")
async def search_patients(query: str):
    """Search for patients by name or identifier.

    This wraps the ORWPT SELECT RPC.
    """
    broker = RPCBroker("localhost", 9430)

    try:
        broker.connect()
        broker.login(access_code=ACCESS, verify_code=VERIFY)
        broker.set_context("OR CPRS GUI CHART")

        # Call RPC
        result = broker.call_rpc("ORWPT SELECT", [query])

        # Parse and format as JSON
        patients = [parse_patient_search_result(line) for line in result]

        return {"patients": patients}

    finally:
        broker.disconnect()

@app.get("/api/patients/{ien}")
async def get_patient(ien: int):
    """Get patient details by IEN.

    This wraps ORWPT ID INFO and other RPCs.
    """
    # Similar pattern...
    pass
```

**Benefits of this approach**:
- **Modern clients** (React, mobile apps) can use standard REST
- **Authentication** can use modern tokens (JWT) at the FastAPI layer
- **Business logic** still enforced by VistA RPCs
- **Caching** can be added at the FastAPI layer
- **Rate limiting**, logging, monitoring are easier

### When to Use RPCs vs. Direct Global Access

| Scenario | Approach | Reason |
|----------|----------|--------|
| **Production patient care app** | RPCs | Business logic, security, validation required |
| **Read-only reporting** | Direct globals | Faster, simpler, no authentication needed |
| **Order entry, clinical workflow** | RPCs | Must enforce VistA's complex rules |
| **Data warehouse ETL** | Direct globals | Bulk read access, no writes |
| **Learning/exploration** | Direct globals (current approach) | Simplicity, visibility into data structure |
| **Future web UI (production)** | RPCs | Safety, proper VistA integration |

**Your current learning scripts** use direct global access because:
1. ✅ You're only reading data
2. ✅ You want to understand the underlying structure
3. ✅ No need for authentication complexity yet
4. ✅ No risk of violating business rules (read-only)

**Your future FastAPI UI** should use RPCs because:
1. ✅ It may need write operations eventually
2. ✅ Business logic validation is critical for patient safety
3. ✅ Authentication and authorization are required
4. ✅ Integration with existing VistA workflows

---

## Deep Dive: How an RPC Call Works Internally

Let's trace a complete RPC call from client to database:

### Step-by-Step: ORWPT SELECT("SMITH")

```
1. CLIENT (CPRS or your Python code)
   └─> Sends RPC Broker protocol message
       RPC: ORWPT SELECT
       Params: ["SMITH"]

2. RPC BROKER (VistA TCP listener on port 9430)
   ├─> Receives protocol message
   ├─> Validates authentication (DUZ set)
   ├─> Validates context (menu option)
   └─> Looks up RPC in ^XWB(8994)
       ^XWB(8994, "B", "ORWPT SELECT") → IEN
       ^XWB(8994, IEN, 0) → "ORWPT SELECT^SELPT^ORWPT^..."

3. M ROUTINE (ORWPT.m, tag SELPT)
   └─> Executes: DO SELPT^ORWPT(.RESULT, "SMITH")

4. M CODE (simplified)
   SELPT(RESULT, SEARCH)
     NEW IEN, NAME, CNT
     SET CNT=0

     ; Search by name in ^DPT "B" index
     SET NAME=$ORDER(^DPT("B", SEARCH))

     FOR  QUIT:NAME=""  DO
       . SET IEN=$ORDER(^DPT("B", NAME, ""))
       . ; Get patient data from ^DPT(IEN, 0)
       . SET DATA=^DPT(IEN, 0)
       . SET CNT=CNT+1
       . ; Format result: IEN^NAME^SSN^DOB^SEX
       . SET RESULT(CNT)=IEN_"^"_$P(DATA,"^",1)_"^"_$P(DATA,"^",9)_"^"...
       . SET NAME=$ORDER(^DPT("B", NAME))

     SET RESULT(0)=CNT  ; First element is count
     QUIT

5. RPC BROKER
   └─> Takes RESULT array, formats per broker protocol
       Sends back to client

6. CLIENT
   └─> Parses broker response
       Returns array of patient lines
```

**Key insight**: RPCs are just **M subroutines with a standardized calling convention** wrapped in broker protocol.

---

## Key Takeaways

1. **RPCs are VistA's API layer** - like REST endpoints, but procedure-oriented
2. **RPC Broker protocol** is complex but client libraries handle it
3. **RPCs call M routines** - you can read the source code to understand them
4. **Authentication + Context required** for production use
5. **Read-only RPCs are safe** for learning (ORWPT*, XUS GET*, etc.)
6. **Direct global access is simpler** for read-only exploration (your current approach)
7. **Future production UIs should use RPCs** for safety and business logic
8. **M direct mode is the easiest way** to test RPC routines during learning

---

## Next Steps

**Right Now**:
1. Complete Exercise 1: List patient-related RPCs
2. Complete Exercise 2: Trace ORWPT SELECT to its M code
3. Complete Exercise 3: Call an RPC in M direct mode

**This Week**:
- Read the M source code for ORWPT routines
- Explore other RPC namespaces (XUS*, ORWDX*)
- Experiment with calling simple RPCs from M

**This Month**:
- Research Python RPC Broker client libraries (PyVistA)
- Design a FastAPI wrapper for read-only patient RPCs
- Consider authentication strategy (test credentials vs. production)

**Future** (Phase 6: Modern UI):
- Implement FastAPI → RPC Broker integration
- Build React/HTMX frontend consuming FastAPI endpoints
- Replace direct global access with RPC calls for production safety

---

## Questions to Explore

As you learn about RPCs, track these questions:

### RPC Architecture Questions
- How does VistA handle concurrent RPC calls from multiple CPRS clients?
- What happens if an RPC crashes mid-execution?
- How are RPC versions managed when VistA is upgraded?

### Security Questions
- How are Access/Verify codes encrypted in the broker protocol?
- Can you call an RPC without setting context? (Answer: Some yes, most no)
- What's the difference between DUZ and DUZ(0)?

### Integration Questions
- Can non-M languages create new RPCs? (Yes, but requires M wrapper)
- How do you test RPCs without a full CPRS client?
- What's the performance difference between RPCs and direct global access?

Add your own as you explore!

---

## References

### VistA Documentation
- VistA RPC Broker Documentation: https://www.va.gov/vdl/application.asp?appid=82
- Remote Procedure File (#8994): Search VistA Data Dictionary
- CPRS Technical Manual: Describes common RPCs used by GUI

### Code Examples
- Your script: `app/04_rpc_explorer.py` (demonstrates RPC inspection)
- M routines: `/home/vehu/r/*.m` (in VEHU container, search for ORWPT, ORWDX, XUS)

### External Resources
- PyVistA: Python RPC Broker client (check GitHub/OSEHR)
- VistA Expertise Network: Community forums with RPC discussions
- OSEHRA: Open source VistA resources and documentation

---

## Appendix: Common RPC Naming Conventions

VistA RPCs follow naming patterns based on package/namespace:

| Prefix | Package | Purpose |
|--------|---------|---------|
| **ORWPT** | CPRS Patient | Patient selection, demographics |
| **ORWDX** | CPRS Orders | Order dialogs, quick orders |
| **ORWOR** | CPRS Orders | Order entry, results |
| **ORWPS** | CPRS Pharmacy | Medications, pharmacy orders |
| **ORQQVI** | CPRS Vitals | Vital signs data |
| **XUS** | Kernel (core) | User authentication, security |
| **XWB** | RPC Broker | Broker utilities, connection |
| **GMV** | Vitals | Vitals package core |
| **PXRM** | Reminders | Clinical reminders |
| **TIU** | Text Integration Utility | Clinical notes, documents |

**Pattern**: `PACKAGE + Function + Verb`
- Example: `ORWPT SELECT` = **OR**der entry **W**indows **P**a**T**ient **SELECT**
