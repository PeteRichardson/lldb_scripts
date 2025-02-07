def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f sections.sections sections')

import os
import sys
import argparse
from functools import lru_cache

try:
    # make lldb module available
    sys.path.append('/Library/Developer/CommandLineTools/Library/PrivateFrameworks/LLDB.framework/Versions/A/Resources/Python')
    import lldb
    from tabulate import tabulate
except ImportError as exc:
    raise ImportError(
        "# ERROR: Missing a library. Run 'pip3 install tabulate'"
    ) from exc


def validate_binary(path):
    if os.path.exists(path) == False:
        raise argparse.ArgumentTypeError(f"'{path}' does not exist.")
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"'{path}' is not a file.")
    return path

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='List sections in a binary file (executable, shared library, object file, etc.) using lldb'
    )
    parser.add_argument('-c', '--csv',
        action='store_true',
        help='output in csv format'
    )
    parser.add_argument('-d',
        '--dependencies',
        action='store_true',
        help='also examine dependent binaries'
    )
    parser.add_argument('-k',
        '--skip-subsections',
        action='store_true',
        help='do not list subsections'
    )
    
    result_args = parser.parse_args(argv)
    return result_args

@lru_cache(None)
def get_section_type_name(section_type):
    for name in dir(lldb):
        if name.startswith("eSectionType") and getattr(lldb, name) == section_type:
            return name[12:]   # remove eSectionType prefix
    return "Unknown"

def build_section(sec: lldb.SBSection, module_name:str):
    '''Return a tuple  containing info about one section'''
    sec_type = sec.GetSectionType()
    sec_type_str  = get_section_type_name(sec_type)
    segment = ""
    if sec_type ==  lldb.eSectionTypeContainer:
        segment = sec.name
    else:
        segment = sec.GetParent().name

    startaddr = sec.GetFileAddress()
    endaddr = startaddr + sec.size

    return [
        f"{hex(int(startaddr))}",
        f"{hex(int(endaddr))}",
        f"{hex(int(sec.size))}",
        module_name, segment, sec.name, sec_type_str]

def get_sections(args, debugger):
    '''Return a list of section tuples'''
    target = lldb.debugger.GetSelectedTarget()
    if not target:
        print("No target selected.")
    else:
        exe_path = target.executable.fullpath  # Get the executable path
        # Close the existing target
        lldb.debugger.DeleteTarget(target)
        # Reopen the target with proper setting for add_dependent_modules
        target = target = debugger.CreateTarget (exe_path, None, None, args.dependencies, lldb.SBError())

    seclist = []
    if target:
        for module in target.module_iter():
            module_name = os.path.basename(str(module.GetFileSpec()))
            for sec in module.section_iter():
                seclist.append(build_section(sec, module_name))
                if not args.skip_subsections:
                    for subsec in sec:
                        seclist.append(build_section(subsec, module_name))
        return seclist
    else:
        print("# Failed to create target.  Check the filetype.", file=sys.stderr)       

headers = ["start","end","size","module","segment","section","type"]

def dump_sections(args, seclist):
    if args.csv:
        dump_sections_csv(args, seclist)
    else:
        dump_sections_table(args, seclist)

def dump_sections_csv(args, seclist):
    '''dump section list as csv'''
    print(",".join(headers))

	# get max lengths for formatting
    maxlens = [0] * len(headers)
    for sec in seclist:
        for i in [0,1,2]:
            maxlens[i] = max(maxlens[i], len(str(sec[i])))
    
    for sec in seclist:
        print(f"{sec[0]: >{maxlens[0]}}", end="")
        print(f",{sec[1]: >{maxlens[1]}}", end="")
        print(f",{sec[2]: >{maxlens[2]}}", end="")
        print(f",{sec[3]}", end="")
        print(f",{sec[4]}", end="")
        print(f",{sec[5]}", end="")
        print(f",{sec[6]}", end="")
        print()

def dump_sections_table(args, seclist):
     alignment = ("right", "right", "right", "left", "left", "left", "left")
     print(tabulate(seclist, headers, tablefmt="simple", colalign=alignment))

def sections(debugger, command, result, internal_dict):
    args = parse_args(command.split())
    sections = get_sections(args, debugger)
    dump_sections(args, sections)