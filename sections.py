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
    parser.add_argument('-d', '--decimal',
        action='store_true',
        help='output addresses and sizes in decimal (default is hex)'
    )
    parser.add_argument('-a', '--all',
        dest='dependencies',
        action='store_true',
        help='include all dependent binaries'
    )
    parser.add_argument('-s', '--skip-subsections',
        action='store_true',
        help='do not list subsections (list only container sections (i.e. segments))'
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

    return [startaddr, endaddr, sec.size, module_name, segment, sec.name, sec_type_str]

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


def dump_sections(args, seclist):
    headers = ["start","end","size","module","segment","section","type"]

    if not args.decimal:   # to hex at the last minute
        for sec in seclist:
            sec[0] = hex(sec[0])
            sec[1] = hex(sec[1])
            sec[2] = hex(sec[2])

    if args.csv:
        print(",".join(headers))
        for sec in seclist:
            print(f"{sec[0]},{sec[1]},{sec[2]},{sec[3]},{sec[4]},{sec[5]},{sec[6]}")
    else:
        alignment = ("right", "right", "right", "left", "left", "left", "left")
        print(tabulate(seclist, headers, tablefmt="simple", colalign=alignment))

def sections(debugger, command, result, internal_dict):
    args = parse_args(command.split())
    sections = get_sections(args, debugger)
    dump_sections(args, sections)