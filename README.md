# SimpleProgramming

This project defines a simple computer as a combination of *Arithmetic Processing Unit* and the *Memory* available as cells labeled from 1,2,... onwards, which store integers. This machine has a set of instructions which has been reduced to a minimum while still allowing it to solve fairly general problems.

## Instruction Set

    Arithmetic
    ----------
    ADD MX MY MZ - MZ := MX + MY
    SUB MX MY MZ - MZ := MX - MY
    MUL MX MY MZ - MZ := MX * MY
    DIV MX MY MZ - MZ := MX / MY

    Unconditional Branching
    -----------------------
    GOT LX       - Goto line LX

    Conditional Branching
    ---------------------
    IFE MX MY LZ - if MX equals MY, goto line LZ
    IFN MX MY LZ - if MX not equals MY, goto line LZ
    IFG MX MY LZ - if MX > MY, goto line LZ
    IFL MX MY LZ - if MX < MY, goto line LZ

    Memory interaction
    ------------------
    PUT MX MY    - M[MY] := MX
    GET MX MY    - MY := M[MX]
    COP MX MY    - MY := MX
    SET A MY     - MY := A


## Sample Programs
Look at sample programs in /sample_programs directory

## To Run
    python3 run_program.py <program_file_name> <optional:debug>

