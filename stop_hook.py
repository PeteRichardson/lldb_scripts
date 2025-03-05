import re
import lldb
from tabulate import tabulate

def remove_first_line(text):
    lines = text.splitlines()
    return "\n".join(lines[1:])  # Join all lines except the first

class PSH:
    def __init__(self, target, extra_args, internal_dict):
        pass

    def format_grid(self, text_blocks, max_width=160):
        """Formats 4 blocks of text into a 2x2 grid with automatic column sizing."""
        if len(text_blocks) != 4:
            raise ValueError("Must provide exactly 4 text blocks.")
        table_data = [
            [text_blocks[0], text_blocks[1]],
            [text_blocks[2], text_blocks[3]]
        ]
        return tabulate(table_data, tablefmt="grid")
    

    def handle_stop(self, exe_ctx, stream):
        """Executed when LLDB stops (e.g., breakpoint, stepping)."""

        debugger = exe_ctx.GetTarget().GetDebugger()

        def run_lldb_cmd(cmd):
            """Runs an LLDB command and returns its output."""
            output = lldb.SBCommandReturnObject()
            debugger.GetCommandInterpreter().HandleCommand(cmd, output)
            return output.GetOutput().strip()

        # Get register values (PC, SP, LR, X0-X9, Z0-Z9 if available)
        registers_cmd = "register read pc sp x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 x10 fp lr"
        registers_output = ".     " + run_lldb_cmd(registers_cmd)
        #registers_output = remove_first_line(registers_output)
        stack_frame_output = run_lldb_cmd("memory read -f A -c 16 -s 8 -- $SP")
        source_output = run_lldb_cmd("source list -a $PC -c 10")
        source_output = remove_first_line(source_output)
        disassembly_output = run_lldb_cmd("disassemble -p -c 10")

        text_blocks = [registers_output, stack_frame_output, disassembly_output, source_output]

        # Print the formatted table
        stream.Print(self.format_grid(text_blocks))
        stream.Print("\n")
                     
# Auto-load the script in LLDB
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command alias psh target stop-hook add -P stop_hook.PSH')
