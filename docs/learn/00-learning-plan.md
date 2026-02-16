# VistA/YottaDB Learning Plan

**Focus**: VistA architecture, patient data structures, and M language fundamentals
**Approach**: Hands-on exploration with read-only scripts, then progressive exercises
**Timeline**: Self-paced, depth over speed

## Learning Objectives

### Phase 1: YottaDB Fundamentals (Current)
- 🔄 Understand global-based hierarchical database model
- 🔄 Master Key/subscript access patterns in Python
- 🔄 Learn intrinsic special variables (ISVs)
- 🔄 Recognize node vs. tree structure differences from traditional databases
- 🔄 Understand `$ORDER()` traversal patterns

### Phase 2: VistA Architecture (In Progress)
- 🔄 Understand FileMan as VistA's data abstraction layer
- 🔄 Learn to navigate the data dictionary (`^DIC`, `^DD`)
- 🔄 Understand the "0-node" metadata pattern
- 🔄 Learn VistA's self-documenting structure
- 🔄 Map major VistA subsystems (patient, providers, orders, pharmacy, lab)

### Phase 3: Core Files Deep Dive (Current)
- 🎯 Explore File #2 (PATIENT) structure in detail
- 🎯 Understand patient identifiers (IEN, SSN, ICN, DFN)
- 🎯 Parse demographics from `^DPT` global
- 🎯 Explore File #200 (NEW PERSON) for providers/users
- 🎯 Understand provider identifiers and person classes
- 🎯 Trace pointers between File #2 and File #200
- 🎯 Understand piece notation and field parsing across files
- 🎯 Practice pointer traversal patterns (one-to-one, one-to-many)

### Phase 4: M Language Literacy (Parallel to Phase 2-3)
- 🎯 Read basic M syntax and control structures
- 🎯 Understand M-specific idioms (`$ORDER`, `$PIECE`, `$GET`, etc.)
- 🎯 Translate common M patterns to Python equivalents
- 🎯 Read existing VistA routines for patient data access

### Phase 5: VistA RPC Interface (Current)
- 🎯 Understand RPC Broker protocol and architecture
- 🎯 Explore RPC definitions in File #8994
- 🎯 Trace RPCs to underlying M routines
- 🎯 Learn common patient/order/clinical RPCs
- 🎯 Understand authentication and context requirements
- 🎯 Compare RPC approach vs. direct global access

### Phase 6: Write Operations (Future)
- 🔲 Safe write patterns with test globals (`^ZZTEST`)
- 🔲 FileMan API for validated writes
- 🔲 Transaction patterns and error handling
- 🔲 Calling VistA business logic routines via RPCs

### Phase 7: Modern UI (Long-term Goal)
- 🔲 FastAPI endpoints wrapping VistA RPCs
- 🔲 HTMX + Jinja2 for progressive enhancement
- 🔲 Modern patient data browser
- 🔲 Replace "roll-and-scroll" interface

**Legend**: ✅ Complete | 🔄 In Progress | 🎯 Next | 🔲 Future

---

## Learning Path Sequence

Follow these documents and exercises in order:

### 1. YottaDB Fundamentals
- **Read**: `01-yottadb-fundamentals.md`
- **Practice**: Run `app/01_env_check.py` with different globals
- **Exercise**: `exercises/ex01-explore-key-patterns.md`

### 2. FileMan Architecture
- **Read**: `02-fileman-architecture.md`
- **Practice**: Run `app/02_list_globals.py` and study the fallback mechanisms
- **Hands-on**: Use the exercises in the doc to discover files and fields

### 3. M Language Primer
- **Read**: `03-m-language-primer.md`
- **Reference**: `reference/m-to-python-patterns.md` (keep this open while reading M code)
- **Practice**: Read simple M routines in VistA

### 4. VistA Patient Data (File #2)
- **Read**: `04-vista-patient-data.md`
- **Practice**: Run `app/03_explore_allowlisted.py --global ^DPT`
- **Hands-on**: Create the patient parser from the doc

### 4b. VistA NEW PERSON File (File #200)
- **Read**: `04b-vista-new-person-file.md`
- **Practice**: Add `^VA` to allowlist, explore `^VA(200,`
- **Hands-on**: Create the user parser from the doc

### 5. VistA Pointers and Relations
- **Read**: `05-vista-pointers-relations.md`
- **Exercise**: `exercises/ex01-explore-file-2-and-200.md` (comprehensive hands-on)
- **Practice**: Patient→Provider pointer traversal

### 6. VistA RPC Broker Interface
- **Read**: `06-vista-rpc-broker.md`
- **Practice**: Run `app/04_rpc_explorer.py --prefix ORWPT --limit 10`
- **Hands-on**: Inspect RPC definitions, trace RPCs to M routines
- **Experiment**: Call simple RPCs in M direct mode

---

## Key Resources

### Documentation You've Created
- `/docs/guide/vista-vehu-docker-guide.md` - How to run VEHU container
- `/docs/guide/yottadb-python-vehu-readonly-lab.md` - Step-by-step Python setup
- `/docs/spec/med-ydb-new-thread-handoff.md` - Technical context from previous work

### Scripts You've Built
- `app/01_env_check.py` - Teaches: ISVs, Key objects, node access
- `app/02_list_globals.py` - Teaches: Multiple discovery methods, FileMan structure, M fallback
- `app/03_explore_allowlisted.py` - Teaches: Safe exploration, allowlists, bounds
- `app/04_rpc_explorer.py` - Teaches: RPC definitions, tracing to M routines, VistA's API layer

### External Resources
- YottaDB Documentation: https://docs.yottadb.com/
- VistA Documentation: https://www.va.gov/vdl/
- FileMan Documentation: https://www.va.gov/vdl/application.asp?appid=5
- M Language: https://docs.yottadb.com/ProgrammersGuide/

---

## Learning Method: Exploration-Driven

### The Cycle
1. **Read** concept documentation
2. **Run** existing scripts to see concepts in action
3. **Modify** scripts to test understanding
4. **Exercise** with structured challenges
5. **Document** discoveries and insights

### Example: Learning About File #2 (PATIENT)

**Step 1**: Run global listing
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/02_list_globals.py --prefix ^DPT --limit 10'
```

**Step 2**: Explore the data dictionary entry
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^DIC --subscript 2'
```

**Step 3**: Look at actual patient records
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^DPT --max-nodes 5'
```

**Step 4**: Document what you learned
- What fields are in the 0-node?
- What subscripts exist under a patient record?
- Where do pointers point?

**Step 5**: Build a custom tool
- Create `app/04_patient_browser.py` to parse demographics cleanly

---

## Measuring Progress

### You'll Know You Understand YottaDB When:
- [ ] You can explain the difference between a node value and a subscript tree
- [ ] You can navigate any global using `$ORDER()` logic
- [ ] You understand when to use `.value` vs. `.subscripts`
- [ ] You can debug YDBError exceptions

### You'll Know You Understand FileMan When:
- [ ] You can look up any global's FileMan file number
- [ ] You can read `^DD` to understand field definitions
- [ ] You understand pointer notation and can trace references
- [ ] You can parse a 0-node's pieces into named fields

### You'll Know You Understand M Language When:
- [ ] You can read a simple M routine and understand control flow
- [ ] You recognize common M functions (`$ORDER`, `$PIECE`, `$GET`, `$DATA`)
- [ ] You can translate M code patterns to Python equivalents
- [ ] You can predict what a M code snippet will do

### You'll Know You Understand VistA Patient Data When:
- [ ] You can explain the difference between IEN, DFN, SSN, and ICN
- [ ] You can extract demographics from `^DPT(patient, 0)`
- [ ] You can trace patient → provider → clinic relationships
- [ ] You understand how VistA maintains patient identity

### You'll Know You Understand VistA RPC Interface When:
- [ ] You can explain the difference between RPCs and direct global access
- [ ] You can find RPC definitions in File #8994 and trace them to M routines
- [ ] You understand RPC Broker protocol and authentication/context requirements
- [ ] You can identify common RPC namespaces (ORWPT, XUS, ORWDX)
- [ ] You understand when to use RPCs vs. direct global access for applications

---

## Next Steps

**Right Now**:
1. Read `01-yottadb-fundamentals.md` to solidify database concepts
2. Read `03-m-language-primer.md` to prepare for reading VistA code
3. Read `04-vista-patient-data.md` to focus on your primary interest area
4. Read `06-vista-rpc-broker.md` to understand VistA's API layer (bridges to modern UI)

**This Week**:
- Complete Exercise 1: Map File #2 structure
- Complete Exercise 2: Parse a patient 0-node
- Explore RPC definitions using `app/04_rpc_explorer.py`
- Trace an RPC to its M routine and understand what it does

**This Month**:
- Build a custom patient data browser script
- Read actual VistA M routines related to patient registration
- Understand pointer chains from patient to provider to clinic

**Future**:
- Explore other VistA domains (orders, pharmacy, lab)
- Learn write patterns with test globals
- Begin FastAPI wrapper design

---

## Questions to Track

As you learn, keep a list of questions. Examples:

### YottaDB Questions
- How does YottaDB handle concurrent access to the same global?
- What are transactions in YottaDB (`TSTART`/`TCOMMIT`)?
- How does replication work?

### VistA Questions
- How does VistA merge duplicate patient records?
- What's the relationship between File #2 and File #2.01 (sub-files)?
- How are deleted records handled (soft delete vs. purge)?

### M Language Questions
- What does the `NEW` command do?
- How do M's scoping rules differ from Python?
- What are "naked references" and why are they problematic?

Add your own as you explore!

---

## Notes and Discoveries

Use this space (or create dated journal files) to record insights:

**2026-02-14**:
- Discovered that `02_list_globals.py` has three fallback mechanisms - shows defensive programming
- FileMan stores global roots in `^DIC(file#, 0, "GL")` - this is the key to mapping files to globals
- VEHU's Python 3.6 lacks modern yottadb binding features - explains compatibility workarounds in scripts

*(Continue adding dated entries as you learn)*
