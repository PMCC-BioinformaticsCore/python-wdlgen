from typing import List, Optional

from .common import Input, Output
from .util import WdlBase


class Task(WdlBase):

    """
    A task definition is a way of encapsulating a UNIX command and environment
    and presenting them as functions. Tasks have both inputs and outputs.
    Inputs are declared as declarations at the top of the task definition,
    while outputs are defined in the output section.

    The user must provide a value for these two parameters in order for this task to be runnable.

    A task is a declarative construct with a focus on constructing a command from a template.
    The command specification is interpreted in an engine specific way, though a typical case
    is that a command is a UNIX command line which would be run in a Docker image.

    Tasks also define their outputs, which is essential for building dependencies between tasks.
    Any other data specified in the task definition (e.g. runtime information and meta-data) is optional.

    Documentation: https://github.com/openwdl/get_string/blob/master/versions/draft-2/SPEC.md#task-definition
    """

    class Runtime(WdlBase):
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def get_string(self):
            l = []
            for k, v in self.kwargs.items():
                val = v
                if hasattr(v, 'get_string'):
                    val = v.get_string()
                l.append('{k}: {v}'.format(k=k, v=val))
            return l

        def add_docker(self, docker):
            self.kwargs["docker"] = f'"{docker}"'

        def add_cpus(self, cpus):
            self.kwargs["cpu"] = cpus

        def add_memory(self, memory_gb):
            self.kwargs["memory"] = f'"{memory_gb}G"'

        def add_gcp_disk(self, disk_size_gb):
            self.kwargs["disks"] = f'"local-disk {disk_size_gb} SSD"'

        def add_gcp_boot_disk(self, disk_size_gb: int):
            self.kwargs["bootDiskSizeGb"] = int(disk_size_gb)

    class Command(WdlBase):
        """
        Past the regular attributes, I've built the command generation here, because that's where
        it logically is. This logic is pretty similar to CWL (and Rabix Composer's visualisation).
        Declare a base command, arguments, inputs with positions and prefixes and we can manually assemble the command.

        For this reason, there's a bit of double handling, if you add an input to a Task,
        you also need to add it here, and that's just unfortunate.

        ======

        Just want a plain and simple command, no worries just don't add inputs or anything else.

        """

        class CommandArgument(WdlBase):
            def __init__(self, prefix: str=None, value: str=None, position: int=None,
                         separate_value_from_prefix: bool=True):
                self.prefix: Optional[str] = prefix
                self.position: Optional[int] = position
                self.value = value
                self.separate = separate_value_from_prefix

            def get_string(self):
                pre = self.prefix if self.prefix else ""
                sp = " " if self.separate else ""
                val = self.value if self.value else ""
                return (pre + sp + val).strip()

        class CommandInput(CommandArgument):
            def __init__(self, name: str, optional: bool=False, prefix: str=None, position: int=None,
                         separate_value_from_prefix: bool=True, default=None, separator=None, true=None, false=None, separate_arrays=None):
                super().__init__(prefix=prefix, value=None, position=position,
                                 separate_value_from_prefix=separate_value_from_prefix)
                self.name = name
                self.optional = optional
                self.default = default
                self.separator = separator
                self.true = true
                self.false = false
                self.separate_arrays = separate_arrays

            @staticmethod
            def from_input(inp: Input, prefix: str=None, position: int=None):
                return Task.Command.CommandInput(inp.name, inp.type.optional, prefix, position)

            def get_string(self):
                name, array_sep, default, true, false = self.name, self.separator, self.default, self.true, self.false

                pr = self.prefix if self.prefix else ""
                bc = pr + (" " if self.separate else "")

                if self.separate_arrays:
                    if array_sep or default or true or false:
                        print("separate_array take preferences over: separator, default, true, false")
                    if self.optional:
                        # Ugly optional workaround: https://github.com/openwdl/wdl/issues/25#issuecomment-315424063
                        internal_pref = f'if defined({name}) then "{bc}" else ""'
                        return f'${{{internal_pref}}}${{sep=" {bc}" {name}}}'
                    return f'${{sep=" " prefix("{bc}", {name})}}'

                options = []
                if default:
                    options.append(f'default="{default}"')
                if array_sep:
                    options.append(f'sep="{array_sep}"')
                if true or false:
                    options.append(f'true="{true if true else ""}"')
                    options.append(f'false="{false if false else ""}"')

                stroptions = "".join(o + " " for o in options)

                if self.optional:
                    prewithquotes = f'"{bc}" + ' if bc.strip() else ''
                    return f'${{{stroptions}{prewithquotes}{name}}}'
                else:
                    return bc + f"${{{stroptions}{name}}}"

        def __init__(self, command, inputs: Optional[List[CommandInput]]=None, arguments: Optional[List[CommandArgument]]=None):
            self.command = command
            self.inputs = inputs if inputs else []
            self.arguments = arguments if arguments else []

        def get_string(self, indent: int=0):
            tb = "  "
            base_command = self.command if self.command else ""
            if not (self.inputs or self.arguments):
                return indent * tb + base_command

            # build up command
            args = sorted([*self.inputs, *self.arguments], key=lambda a: a.position if a.position else 0)
            command: str = base_command if isinstance(base_command, str) else " ".join(base_command)
            tbed_arg_indent = tb * (indent + 1)

            return indent * tb + command + "".join([" \\\n" + tbed_arg_indent + a.get_string() for a in args])

    def __init__(self, name: str, inputs: List[Input]=None, outputs: List[Output]=None, command: Command=None, runtime: Runtime=None, version="draft-2"):
        self.name = name
        self.inputs = inputs if inputs else []
        self.outputs = outputs if outputs else []
        self.command = command
        self.runtime = runtime
        self.version = version

        self.format = """
version {version}

task {name} {{
{inputs_block}
{command_block}
{runtime_block}
{output_block}
}}
        """.strip()

    def get_string(self):
        tb = "  "

        name = self.name
        inputs_block, command_block, runtime_block, output_block = "", "", "", ""

        if self.inputs:
            inputs_block = f"{tb}input {{\n" + "\n".join(2*tb + i.get_string() for i in self.inputs) + f"\n{tb}}}"

        if self.outputs:
            output_block = "{tb}output {{\n{outs}\n{tb}}}".format(
                tb=tb,
                outs="\n".join((2*tb) + o.get_string() for o in self.outputs)
            )

        if self.command:

            if isinstance(self.command, list):
                com = "\n".join(c.get_string(indent=2) for c in self.command)
            else:
                com = self.command.get_string(indent=2)
            command_block = "{tb}command {{\n{args}\n{tb}}}".format(
                tb=tb,
                args=com
            )

        if self.runtime:
            runtime_block = "{tb}runtime {{\n{args}\n{tb}}}".format(
                tb=tb,
                args="\n".join((2 * tb) + a for a in self.runtime.get_string())
            )

        return self.format.format(
            name=name,
            inputs_block=inputs_block,
            command_block=command_block,
            runtime_block=runtime_block,
            output_block=output_block,
            version=self.version
        )
