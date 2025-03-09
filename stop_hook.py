import re
import shutil

import lldb
from tabulate import tabulate


def remove_first_line(text):
    lines = text.splitlines()
    return "\n".join(lines[1:])  # Join all lines except the first

def truncate_lines(text: str, max_length: int) -> str:
    """Truncate each line in a multiline string to max_length characters."""
    return "\n".join(line[:max_length] for line in text.splitlines())

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def ensure_ansi_reset(text: str) -> str:
    """Ensures each line in a multiline string ends with an ANSI reset escape sequence (\x1b[0m)."""
    RESET = "\x1b[0m"
    return "\n".join([line + RESET if not line.endswith(RESET) else line for line in text.splitlines()])

class PSH:
    def __init__(self, target, extra_args, internal_dict):
        debugger = target.GetDebugger()
        debugger.HandleCommand("settings set stop-line-count-before 0")
        debugger.HandleCommand("settings set stop-line-count-after 0")
        debugger.HandleCommand("settings set stop-disassembly-count 0")

    def format_grid(self, text_blocks):
        """Formats 4 blocks of text into a 2x2 grid with automatic column sizing."""
        if len(text_blocks) != 4:
            raise ValueError("Must provide exactly 4 text blocks.")
        table_data = [
            [text_blocks[0], text_blocks[1]],
            [text_blocks[2], text_blocks[3]]
        ]
        return tabulate(table_data, tablefmt="fancy_grid")
    
    def format_registers(self, registers: str):
        """
        Slightly improves the output of the "register read" command.
        Right-justifies the text before the equals sign.
        """
        result = ""
        for line in registers.splitlines():
            r,v = line.strip().split(" = ")
            result = result + f"{r.rjust(4)} = {v}\n"
        return "REGISTERS\n" + result

    def handle_stop(self, exe_ctx, stream):
        """Executed when LLDB stops (e.g., breakpoint, stepping)."""

        debugger = exe_ctx.GetTarget().GetDebugger()

        def run_lldb_cmd(cmd):
            """Runs an LLDB command and returns its output."""
            output = lldb.SBCommandReturnObject()
            debugger.GetCommandInterpreter().HandleCommand(cmd, output)
            return output.GetOutput().strip()

        screen_width = shutil.get_terminal_size().columns
        max_col_width = (screen_width // 2)

        # Get register values (PC, SP, LR, X0-X9, Z0-Z9 if available)
        registers_cmd = "register read x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 x10 fp lr sp pc cpsr"
        registers_output = run_lldb_cmd(registers_cmd)
        registers_output = self.format_registers(registers_output)
        registers_output = truncate_lines(registers_output, max_col_width)
        stack_output = run_lldb_cmd("memory read -f A -c 16 -s 8 -- $SP")
        stack_frame_output = f"STACK\n{stack_output}"
        stack_frame_output = truncate_lines(stack_frame_output, max_col_width)
        disassembly_output = run_lldb_cmd("disassemble -p -c 10")
        disassembly_output = truncate_lines(disassembly_output, max_col_width)
        disassembly_output = ensure_ansi_reset(disassembly_output)
        source_output = run_lldb_cmd("source list -a $PC -c 10")
        source_output = remove_first_line(source_output)
        source_output = strip_ansi(source_output)
        source_output = source_output.expandtabs(4)
        source_output = truncate_lines(source_output, max_col_width)

        text_blocks = [registers_output, stack_frame_output, disassembly_output, source_output]
        
        # Print the formatted table
        stream.Print(self.format_grid(text_blocks))
        stream.Print("\n")
                     
# Auto-load the script in LLDB
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command alias psh target stop-hook add -P stop_hook.PSH')
