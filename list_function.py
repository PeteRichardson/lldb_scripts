#!/usr/bin/python3

import lldb
import os

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f list_function.list_function lf')

def get_function_by_name(target, function_name):
    """Find a function by name in the target"""
    for module in target.module_iter():
        for symbol in module:
            if symbol.GetType() == lldb.eSymbolTypeCode:
                if symbol.GetName() == function_name:
                    return symbol.GetStartAddress().GetFunction()
    return None

def get_file_line_count(filepath):
    """Get the total number of lines in a file"""
    try:
        with open(filepath, 'r') as f:
            return sum(1 for _ in f)
    except Exception as e:
        return None

def find_next_function_start(target, current_addr):
    """Find the start address of the next function after the given address"""
    next_start = None
    current_offset = current_addr.GetLoadAddress(target)
    
    for module in target.module_iter():
        for symbol in module:
            if symbol.GetType() == lldb.eSymbolTypeCode:
                addr = symbol.GetStartAddress().GetLoadAddress(target)
                if addr > current_offset:
                    if next_start is None or addr < next_start:
                        next_start = addr
    return next_start

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
    
    # Get function start information
    start_addr = function.GetStartAddress()
    if not start_addr:
        result.AppendMessage("Could not determine function start.")
        return
    
    start_line_entry = start_addr.GetLineEntry()
    if not start_line_entry:
        result.AppendMessage("Could not determine source lines.")
        return
    
    source_file = start_line_entry.GetFileSpec()
    start_line = start_line_entry.GetLine()
    
    if not source_file or not start_line:
        result.AppendMessage("Could not get source file information.")
        return
    
    # Try to get end line through various methods
    end_line = None
    
    # Method 1: Try normal end address
    end_addr = function.GetEndAddress()
    if end_addr:
        end_line_entry = end_addr.GetLineEntry()
        if end_line_entry:
            end_line = end_line_entry.GetLine() - 2
    
    # Method 2: If that failed, try to find next function's start
    if not end_line:
        next_func_addr = find_next_function_start(target, start_addr)
        if next_func_addr:
            addr = target.ResolveLoadAddress(next_func_addr)
            if addr:
                line_entry = addr.GetLineEntry()
                if line_entry:
                    end_line = line_entry.GetLine() - 2
    
    # Method 3: If still no end_line, use file length
    if not end_line:
        file_path = os.path.join(source_file.GetDirectory(), source_file.GetFilename())
        total_lines = get_file_line_count(file_path)
        if total_lines:
            end_line = total_lines
    
    if not end_line:
        result.AppendMessage("Could not determine function end line.")
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
                if i < len(lines):  # Protect against EOF
                    result.AppendMessage(f"{lines[i].rstrip()}")
    except Exception as e:
        result.AppendMessage(f"Error reading source file: {str(e)}")

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f list_function.list_function lf')