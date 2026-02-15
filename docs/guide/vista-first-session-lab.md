# VistA First Session Lab (Read-Only)

This lab is for first-time users running VEHU in Docker on macOS.

- Duration: 20-30 minutes
- Goal: learn safe navigation, menu discovery, and basic data inquiry
- Safety: read-only workflow; avoid edit actions

## 1. Intro: Essential Navigation

At VistA prompts, these keys/commands are the foundation:

- `?` shows available options at the current prompt
- `??` shows more detailed help (when available)
- `Enter` accepts a default shown in angle brackets, like `<TEST ACCOUNT>`
- `^` backs out one level (repeat to continue backing out)
- Option names can usually be entered by mnemonic or full text (example: `FM` for FileMan)

Exit behavior depends on context:

- At VistA menu prompts (for example `Select ... Option:`), use `^` to back out and sign off
- At a MUMPS/programmer prompt (`>`), use `HALT` (or `H`) to exit the M process
- If `H` does not exit, you are likely still in menu context; use `^`

## 2. Quick User/Privilege Orientation

Your VEHU login list includes multiple user personas. Exact permissions are controlled by assigned options/keys, but these are good working assumptions:

- `PROGRAMMER,ONE` (`PRO1234`): high privilege, broad system access, can alter system/data
- `PROVIDER,*` accounts: clinician workflows, generally narrower than programmer access
- `PHARMACIST,*` and `LABTECH,*`: domain-focused workflows for pharmacy/lab areas
- Other named users: role-specific access combinations used for testing/demo scenarios

Recommended learning sequence:

1. Start with `PROGRAMMER,ONE` only to learn menu structure
2. Switch to a provider account (for example `PROV40`) to see user-level workflow boundaries
3. Use least-privilege account for realistic application testing whenever possible

## 3. Lab Setup

Start roll-and-scroll:

```bash
docker exec -it vehu su - vehu -c 'mumps -r ZU'
```

Log in with one of the provided Access/Verify pairs.

You should land on something like:

`Select Systems Manager Menu <TEST ACCOUNT> Option:`

## 4. 20-Minute Guided Lab (Read-Only)

### Step A: Discover the current menu (2-3 min)

At the `Select ... Option:` prompt:

1. Enter `?`
2. Enter `??`
3. Note the difference between short and detailed help

Checkpoint:

- You can see option names and understand how to ask for prompt-local help

### Step B: Enter FileMan (5 min)

From the Systems Manager menu prompt:

1. Enter `FM`
2. At the FileMan menu prompt, enter `?`
3. Choose an inquiry-oriented option (typically `Inquire to File Entries`)

If you do not know the exact option name, use `?` and select the inquiry item from the displayed list.

Checkpoint:

- You are inside a read-only inquiry flow (not edit mode)

### Step C: Inquire into common files (8-10 min)

Within inquiry flow:

1. When asked for `Select FILE:`, try `NEW PERSON`
2. Choose an entry and display a standard field set
3. Repeat for `PATIENT`

Tips:

- If prompted for output device, choose screen/terminal defaults
- Use `^` to back out if you enter an unintended prompt

Checkpoint:

- You can successfully navigate file and entry selection without changing data

### Step D: Return to top-level and sign off (2-3 min)

1. Use `^` repeatedly until you return through menus
2. Continue `^` to sign off and return to shell
3. If you ever drop to `>` prompt, use `HALT`

Checkpoint:

- You can exit cleanly from both menu and M prompt contexts

## 5. Common Mistakes and Recovery

- Mistake: entering `H` at menu prompt and expecting exit
  - Recovery: use `^` until sign-off
- Mistake: opening edit options unintentionally
  - Recovery: back out with `^` before filing/saving any changes
- Mistake: getting lost in nested prompts
  - Recovery: `^` step-by-step until you recognize a parent menu

## 6. Optional Follow-Up Exercises

- Repeat this lab with `PROV40` and compare visible menus versus `PROGRAMMER,ONE`
- Explore one domain menu with read-only intent (lab, pharmacy, or HL7) using `?` and inquiry/report options only
- Keep a small "menu path map" as you navigate to build orientation

## 7. Suggested Next Lab Topics

Possible follow-up labs after this one:

1. Provider-focused navigation lab (`PROV40`) and clinical menu orientation
2. FileMan inquiry deep dive (safe reporting patterns)
3. HL7 monitoring/queue visibility lab (read-only)
4. Intro to M prompt utilities for non-destructive inspection
