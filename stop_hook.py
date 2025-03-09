import re
import lldb
from tabulate import tabulate

def remove_first_line(text):
    lines = text.splitlines()
    return "\n".join(lines[1:])  # Join all lines except the first

def format_registers(registers: str):
    """
    Slightly improves the output of the "register read" command.
    Right-justifies the text before the equals sign.
    
    Args:
        text (str): The multiline string to process with format "name = value"
    
    Returns:
        str: A new string with leading whitespace removed, equals signs aligned,
             and names right-justified
    """
    result = ""
    for line in registers.splitlines():
        r,v = line.strip().split(" = ")
        result = result + f"{r.rjust(4)} = {v}\n"
    return "REGISTERS\n" + result

class PSH:
    def __init__(self, target, extra_args, internal_dict):
        debugger = target.GetDebugger()
        debugger.HandleCommand("settings set stop-line-count-before 0")
        debugger.HandleCommand("settings set stop-line-count-after 0")
        debugger.HandleCommand("settings set stop-disassembly-count 0")

    def format_grid(self, text_blocks, max_width=160):
        """Formats 4 blocks of text into a 2x2 grid with automatic column sizing."""
        if len(text_blocks) != 4:
            raise ValueError("Must provide exactly 4 text blocks.")
        table_data = [
            [text_blocks[0], text_blocks[1]],
            [text_blocks[2], text_blocks[3]]
        ]
        return tabulate(table_data, tablefmt="fancy_grid", stralign="left", colalign=("left", "left"))
    

    def handle_stop(self, exe_ctx, stream):
        """Executed when LLDB stops (e.g., breakpoint, stepping)."""

        debugger = exe_ctx.GetTarget().GetDebugger()

        def run_lldb_cmd(cmd):
            """Runs an LLDB command and returns its output."""
            output = lldb.SBCommandReturnObject()
            debugger.GetCommandInterpreter().HandleCommand(cmd, output)
            return output.GetOutput().strip()

        # Get register values (PC, SP, LR, X0-X9, Z0-Z9 if available)
        registers_cmd = "register read x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 x10 fp lr sp pc cpsr"
        registers_output = run_lldb_cmd(registers_cmd)
        registers_output = format_registers(registers_output)
        stack_output = run_lldb_cmd("memory read -f A -c 16 -s 8 -- $SP")
        stack_frame_output = f"STACK\n{stack_output}"
        source_output = run_lldb_cmd("source list -a $PC -c 10")
        source_output = remove_first_line(source_output)
        disassembly_output = run_lldb_cmd("disassemble -p -c 10")

        text_blocks = [registers_output, stack_frame_output, disassembly_output, source_output]

        # Print the formatted table
        stream.Print(self.format_grid(text_blocks))
        stream.Print("\n")
        #return lldb.eReturnStatusSuccessFinishNoResult
                     
# Auto-load the script in LLDB
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command alias psh target stop-hook add -P stop_hook.PSH')
