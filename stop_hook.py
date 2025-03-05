import lldb

class PSH:
    def __init__(self, target, extra_args, internal_dict):
        pass

    def handle_stop(self, exe_ctx, stream):
        """Executed when LLDB stops (e.g., breakpoint, stepping)."""

        debugger = exe_ctx.GetTarget().GetDebugger()

        def run_lldb_cmd(cmd):
            """Runs an LLDB command and returns its output."""
            output = lldb.SBCommandReturnObject()
            debugger.GetCommandInterpreter().HandleCommand(cmd, output)
            return output.GetOutput().strip()

        # Get register values (PC, SP, LR, X0-X9, Z0-Z9 if available)
        registers_cmd = "register read pc sp lr x0 x1 x2 x3 x4 x5 x6 x7 x8 x9"
        registers_output = run_lldb_cmd(registers_cmd)
        stack_frame_output = run_lldb_cmd("frame info")
        source_output = run_lldb_cmd("source list -c 5")
        disassembly_output = run_lldb_cmd("disassemble -c 5")

        # Format into a 2x2 table
        table = f"""
+-----------------------------+-----------------------------+
| Registers                   | Stack Frame                 |
|-----------------------------|-----------------------------|
{registers_output}
|-----------------------------|-----------------------------|
{stack_frame_output}
+-----------------------------+-----------------------------+
| Source Code                 | Disassembly                 |
|-----------------------------|-----------------------------|
{source_output}
|-----------------------------|-----------------------------|
{disassembly_output}
+-----------------------------+-----------------------------+
"""

        # Print the formatted table
        stream.Print(table)

# Auto-load the script in LLDB
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('script from stop_hook import PSH')
    debugger.HandleCommand('command alias psh target stop-hook add -P PSH')