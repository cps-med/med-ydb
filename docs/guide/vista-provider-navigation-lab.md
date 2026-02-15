# VistA Provider Navigation Lab (PROV40, Read-Only)

This lab is a follow-up to the first session lab and focuses on using a provider account.

- Recommended account: `PROVIDER,FORTY` (`PROV40` / `PROV40!!`)
- Duration: 30-45 minutes
- Goal: learn provider-oriented navigation and how to find/view real records
- Safety: read-only workflow; do not sign orders or file edits

## 1. Quick Start

Launch roll-and-scroll:

```bash
docker exec -it vehu su - vehu -c 'mumps -r ZU'
```

Log in as `PROV40`.

## 2. Provider Navigation Fundamentals

Use these at nearly every prompt:

- `?` show valid choices at this prompt
- `??` show more detailed help (when available)
- `Enter` accept default in angle brackets
- `^` back out one prompt/menu level

Exit guidance:

- Menu context: use `^` repeatedly until sign-off
- M prompt (`>`): use `HALT` or `H`

## 3. What to Expect as a Provider

Compared with `PROGRAMMER,ONE`, provider users generally have:

- More clinical workflow menus
- Fewer system-management/programmer options
- Tighter permissions around infrastructure and administrative actions

This is the expected and preferred behavior for realistic workflow testing.

## 4. Lab Part A: Orient to Your Menu Tree (5-10 min)

At your first provider menu prompt:

1. Enter `?`
2. Enter `??`
3. Identify likely clinical/inquiry paths, such as:
   - Patient lookup/inquiry options
   - Order entry/review menus
   - Problem list / notes / labs / meds views

Record 2-3 menu names you want to explore.

## 5. Lab Part B: Find and View a Patient Record (10-15 min)

The exact option names vary by configuration. Use this pattern:

1. From a provider menu, choose a patient-oriented inquiry option.
2. At patient prompts, enter partial names and use `?` when needed.
3. Select a patient and open a read-only view (inquiry/review, not edit).

Common prompt patterns:

- `Select PATIENT NAME:`
- `Select Patient:`
- `Patient Lookup:`

What to inspect once in a patient context:

- Demographics/identifiers
- Active problems
- Medications
- Recent vitals/labs
- Recent notes/encounters

If an option offers edit/sign actions, back out with `^` and choose inquiry/review options instead.

### Patient search strategies when information is incomplete

In most patient lookup prompts (for example `Select PATIENT NAME:`), you can search with partial values:

- `SMITH,JAN` for last name plus partial first name
- `SMITH,J` for last name plus first initial
- `SMITH` followed by `?` to display matching entries
- `??` to see full prompt help and accepted identifier formats

Suggested workflow:

1. Start with a partial name (for example `SMITH,J`)
2. Use `?` to list candidates
3. Refine by typing more characters (for example `SMITH,JAN`)
4. Confirm the correct person using a second identifier before chart review

Second-identifier checks often include:

- Date of birth
- Last 4 of SSN (if shown in your workflow)
- Another site-appropriate patient identifier

Provider expectation:

- You are not expected to know every identifier in advance
- You are expected to positively identify the patient using at least two identifiers before acting on clinical data

## 6. Lab Part C: View Provider/User Records (NEW PERSON) (10 min)

### Preferred provider-safe path

Look for a user/provider inquiry option from your available menus (names vary).

Possible label patterns:

- `Provider Inquiry`
- `User Inquiry`
- `Person Class Inquiry`
- `New Person Inquiry`

Use `?` at each prompt and choose inquiry/display actions only.

### FileMan fallback (if exposed to PROV40)

If your menu includes `FM` (VA FileMan), you can inspect records directly:

1. Enter `FM`
2. Choose `Inquire to File Entries`
3. At `Select FILE:`, enter `NEW PERSON`
4. Select an entry to display fields
5. Repeat with `PATIENT`

If `FM` is not available for `PROV40`, that is normal; continue with provider-facing inquiry menus.

## 7. Lab Part D: View a Clinical Record Slice (10 min)

Pick one clinical area and perform a read-only review:

1. Labs: view recent results for one patient
2. Medications: view active/inactive medication list
3. Notes/encounters: view one recent note metadata and text display if available

Use this discipline:

- Stay in inquiry/review actions
- Do not accept prompts that imply sign/release/file
- Use `^` to retreat if uncertain

## 8. Suggested “Record Lookup Script” for First-Time Providers

Use this simple script each time you explore:

1. Identify current menu (`?`)
2. Enter patient inquiry option
3. Select a known patient
4. View demographics
5. View one domain (labs or meds)
6. Back out with `^`
7. Enter provider/user inquiry path
8. View one `NEW PERSON`-related record (menu-based or FileMan fallback)
9. Exit safely

## 9. Troubleshooting

- `Option not found`:
  - Use `?` and choose from listed options; names differ by site build
- `No such patient`:
  - Try partial names and `?` to browse
- Landed in edit workflow:
  - Back out with `^` before filing/signing
- `H` did not exit:
  - You are likely in menu context; continue with `^`

## 10. Completion Criteria

You have completed this lab when you can:

1. Log in as `PROV40` and orient with `?`/`??`
2. Find and display at least one patient record in a read-only context
3. View at least one clinical data area (labs, meds, or notes)
4. View provider/user-related data (provider inquiry path or `NEW PERSON` via FileMan fallback)
5. Exit cleanly using `^` (and `HALT` only if at `>` prompt)

## 11. Next Lab Ideas

1. Provider chart-review lab: structured walkthrough of meds, problems, allergies, labs
2. Clinical notes lab: note discovery, display, and TIU orientation (read-only)
3. Orders lab (safe mode): understand order dialogs without signing/releasing
