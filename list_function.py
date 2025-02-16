#!/usr/bin/env python

import lldb

def get_function_by_name(target, function_name):
    """Find a function by name in the target"""
    for module in target.module_iter():
        for symbol in module:
            if symbol.GetType() == lldb.eSymbolTypeCode:
                if symbol.GetName() == function_name:
                    function = symbol.GetStartAddress().GetFunction()
                    print(f"{function.name} 0x{function.GetStartAddress()}-0x{function.GetEndAddress()}")
                    return function
    return None

def get_function(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    if not target:
        result.AppendMessage("No target available.")
        return
    
    # Parse command argument
    command = command.strip()
    
    if command:  # Function name provided
        function = get_function_by_name(target, command)
        result.AppendMessage(f"Function: {command}")
        if not function:
            result.AppendMessage(f"Could not find function named '{command}'")
            return

def list_function(debugger, command, result, internal_dict):
    """Lists the entire source code of a function in LLDB.
    Usage: listfunc [function_name]
    If no function name is provided, lists the current function."""
    
    target = debugger.GetSelectedTarget()
    if not target:
        result.AppendMessage("No target available.")
        return
    
    # Parse command argument
    command = command.strip()
    
    if command:  # Function name provided
        function = get_function_by_name(target, command)
        if not function:
            result.AppendMessage(f"Could not find function named '{command}'")
            return
    else:  # No function name - use current function
        process = target.GetProcess()
        if not process:
            result.AppendMessage("No process available.")
            return
            
        thread = process.GetSelectedThread()
        if not thread:
            result.AppendMessage("No thread selected.")
            return
            
        frame = thread.GetSelectedFrame()
        if not frame:
            result.AppendMessage("No frame selected.")
            return
            
        function = frame.GetFunction()
        if not function:
            result.AppendMessage("No function found in current frame.")
            return
        
    # Get function boundaries
    start_addr = function.GetStartAddress()
    end_addr = function.GetEndAddress()
    
    if not start_addr or not end_addr:
        result.AppendMessage("Could not determine function boundaries.")
        return
    
    # Get source file and lines
    start_line_entry = start_addr.GetLineEntry()
    end_line_entry = end_addr.GetLineEntry()
    
    if not start_line_entry:
        result.AppendMessage("Could not determine function starting line.")
        return
    
    
    source_file = start_line_entry.GetFileSpec()
    start_line = start_line_entry.GetLine()
    if end_line_entry:
        end_line = end_line_entry.GetLine() - 1
    else:
        end_line = start_line + 10
    
    if not source_file or not start_line or not end_line:
        result.AppendMessage("Could not get source file information.")
        return
    
    # Print function name and location
    result.AppendMessage(f"Function: {function.GetName()}")
    result.AppendMessage(f"File: {source_file.GetDirectory()}/{source_file.GetFilename()}")
    result.AppendMessage(f"Lines: {start_line}-{end_line}\n")
    
    # Read and display the source lines
    try:
        with open(source_file.GetDirectory() + "/" + source_file.GetFilename(), 'r') as f:
            lines = f.readlines()
            
            # Account for 0-based line numbering in file
            for i in range(start_line - 1, end_line):
                result.AppendMessage(f"{i + 1:4d}: {lines[i].rstrip()}")
    except Exception as e:
        result.AppendMessage(f"Error reading source file: {str(e)}")

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f list_function.list_function lf')
    print('The "lf" command has been installed and is ready for use.')