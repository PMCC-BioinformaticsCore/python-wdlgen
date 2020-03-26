from typing import List, Optional

from .common import Input, Output
from .util import WdlBase, KvClass, Meta, ParameterMeta


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

    class Runtime(KvClass):
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
            def __init__(
                self,
                prefix: str = None,
                value: str = None,
                position: int = None,
                separate_value_from_prefix: bool = True,
            ):
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
            def __init__(
                self,
                name: str,
                optional: bool = False,
                prefix: str = None,
                position: int = None,
                separate_value_from_prefix: bool = True,
                default=None,
                separator=None,
                true=None,
                false=None,
                separate_arrays=None,
            ):
                super().__init__(
                    prefix=prefix,
                    value=None,
                    position=position,
                    separate_value_from_prefix=separate_value_from_prefix,
                )
                self.name = name
                self.optional = optional
                self.default = default
                self.separator = separator
                self.true = true
                self.false = false
                self.separate_arrays = separate_arrays

            @staticmethod
            def from_input(inp: Input, prefix: str = None, position: int = None):
                return Task.Command.CommandInput(
                    inp.name, inp.type.optional, prefix, position
                )

            def get_string(self):
                name, array_sep, default, true, false = (
                    self.name,
                    self.separator,
                    self.default,
                    self.true,
                    self.false,
                )

                prefix = self.prefix if self.prefix else ""
                bc = prefix + (" " if self.separate and self.prefix else "")

                if self.separate_arrays:
                    if array_sep or default or true or false:
                        print(
                            "separate_array take preferences over: separator, default, true, false"
                        )
                    if self.optional:
                        # Ugly optional workaround: https://github.com/openwdl/wdl/issues/25#issuecomment-315424063
                        # Additional workaround for 'length(select_first({name}, [])' as length requires a non-optional array
                        internal_pref = f'if defined({name}) && length(select_first([{name}, []])) > 0 then "{bc}" else ""'
                        return f'~{{{internal_pref}}}~{{sep=" {bc}" {name}}}'
                    return f'~{{sep=" " prefix("{bc}", {name})}}'

                if array_sep and self.optional:
                    # optional array with separator
                    # ifdefname = f'(if defined({name}) then {name} else [])'
                    return f'~{{true="{bc}" false="" defined({name})}}~{{sep="{array_sep}" {name}}}'

                options = []
                if default:
                    val = default
                    if isinstance(default, str):
                        val = f'"{default}"'
                    if isinstance(default, bool):

                        val = "true" if default else "false"
                    options.append(f"default={val}")
                if array_sep:
                    options.append(f'sep="{array_sep}"')
                is_flag = true or false
                if is_flag:
                    options.append(f'true="{true if true else ""}"')
                    options.append(f'false="{false if false else ""}"')

                stroptions = "".join(o + " " for o in options)
                if self.optional and not default and not is_flag and bc.strip():
                    # Option 1: We apply quotes are value, Option 2: We quote whole "prefix + name" combo
                    if self.separate and self.prefix:
                        return f'~{{\'"{prefix}" "\' + {name} + \'"\'}}'
                    else:
                        return f'~{{\'"{prefix}\' + {name} + \'"\'}}'
                else:
                    return bc + f"~{{{stroptions}{name}}}"

        def __init__(
            self,
            command,
            inputs: Optional[List[CommandInput]] = None,
            arguments: Optional[List[CommandArgument]] = None,
        ):
            self.command = command
            self.inputs = inputs if inputs else []
            self.arguments = arguments if arguments else []

        def get_string(self, indent: int = 0):
            tb = "  "
            base_command = self.command if self.command else ""
            if not (self.inputs or self.arguments):
                return indent * tb + base_command

            # build up command
            args = sorted(
                [*self.inputs, *self.arguments],
                key=lambda a: a.position if a.position else 0,
            )
            command: str = base_command if isinstance(base_command, str) else " ".join(
                base_command
            )
            tbed_arg_indent = tb * (indent + 1)

            return (
                indent * tb
                + command
                + "".join([" \\\n" + tbed_arg_indent + a.get_string() for a in args])
            )

    def __init__(
        self,
        name: str,
        inputs: List[Input] = None,
        outputs: List[Output] = None,
        command: Command = None,
        runtime: Runtime = None,
        version="draft-2",
        meta: Meta = None,
        parameter_meta: ParameterMeta = None,
    ):
        self.name = name
        self.inputs = inputs if inputs else []
        self.outputs = outputs if outputs else []
        self.command = command
        self.runtime = runtime
        self.version = version

        self.meta = meta
        self.param_meta = parameter_meta

        self.format = """
version {version}

task {name} {{
{blocks}
}}
        """.strip()

    def get_string(self):
        tb = "  "

        name = self.name
        blocks = []

        if self.inputs:
            blocks.append(
                f"{tb}input {{\n"
                + "\n".join(2 * tb + i.get_string() for i in self.inputs)
                + f"\n{tb}}}"
            )

        if self.command:

            if isinstance(self.command, list):
                com = "\n".join(c.get_string(indent=2) for c in self.command)
            else:
                com = self.command.get_string(indent=2)
            blocks.append("{tb}command <<<\n{args}\n{tb}>>>".format(tb=tb, args=com))

        if self.runtime:
            rt = self.runtime.get_string(indent=2)
            blocks.append(
                "{tb}runtime {{\n{args}\n{tb}}}".format(
                    tb=tb,
                    args=rt,
                )
            )

        if self.meta:
            mt = self.meta.get_string(indent=2)
            if mt:
                blocks.append(
                    "{tb}meta {{\n{args}\n{tb}}}".format(
                        tb=tb, args=mt
                    )
                )

        if self.param_meta:
            pmt = self.param_meta.get_string(indent=2)
            if pmt:
                blocks.append(
                    "{tb}parameter_meta {{\n{args}\n{tb}}}".format(
                        tb=tb,
                        args=pmt
                    )
                )

        if self.outputs:
            blocks.append(
                "{tb}output {{\n{outs}\n{tb}}}".format(
                    tb=tb,
                    outs="\n".join((2 * tb) + o.get_string() for o in self.outputs),
                )
            )

        return self.format.format(
            name=name, blocks="\n".join(blocks), version=self.version
        )
