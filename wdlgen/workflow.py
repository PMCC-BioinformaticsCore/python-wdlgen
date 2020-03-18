from typing import List, Any

from .common import Input, Output
from .util import WdlBase, Meta, ParameterMeta
from .workflowcall import WorkflowCallBase


class Workflow(WdlBase):
    def __init__(
        self,
        name,
        inputs: List[Input] = None,
        outputs: List[str] = None,
        calls: List[WorkflowCallBase] = None,
        imports: List[Any] = None,
        version="draft-2",
        meta: Meta = None,
        parameter_meta: ParameterMeta = None,
    ):
        """

        :param name:
        :param inputs:
        :param outputs:
        :param calls: List[WorkflowXCallBase]
        :param imports:
        :type imports: List[WorkflowImport]
        """

        # validate

        self.name = name.replace("-", "_")
        self.inputs = inputs if inputs else []
        self.outputs = outputs if outputs else []
        self.calls = calls if calls else []
        self.imports = imports if imports else []
        self.version = version

        self.meta = meta
        self.param_meta = parameter_meta

        self.format = """
version {version}

{imports_block}

workflow {name} {{
{blocks}
}}""".strip()

    def get_string(self):
        tb = "  "

        name = self.name
        imports_block = ""
        blocks = []

        if self.inputs:
            ins = []
            for i in self.inputs:
                wd = i.get_string()
                if isinstance(wd, list):
                    ins.extend(2 * tb + ii for ii in wd)
                else:
                    ins.append(2 * tb + wd)
            blocks.append(f"{tb}input {{\n" + "\n".join(ins) + f"\n{tb}}}")

        if self.calls:
            blocks.append("\n".join(c.get_string(indent=1) for c in self.calls))

        if self.imports:
            imports_block = "\n".join(i.get_string() for i in self.imports)

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
            outs = []
            # either str | Output | list[str | Output]
            for o in self.outputs:
                if isinstance(o, Output):
                    wd = o.get_string()
                    if isinstance(wd, list):
                        outs.extend((2 * tb) + w for w in wd)
                    else:
                        outs.append((2 * tb) + wd)
                else:
                    outs.append(str(o))
            blocks.append(
                "{tb}output {{\n{outs}\n{tb}}}".format(tb=tb, outs="\n".join(outs))
            )

        return self.format.format(
            name=name,
            imports_block=imports_block,
            blocks="\n".join(blocks),
            version=self.version,
        )

    class WorkflowImport(WdlBase):
        def __init__(self, name: str, alias: str, tools_dir="tools/"):
            self.name = name
            self.alias = alias
            self.tools_dir = tools_dir

            if tools_dir and not self.tools_dir.endswith("/"):
                tools_dir += "/"

        def get_string(self):
            as_alias = " as " + self.alias if self.alias else ""
            return 'import "{tools_dir}{tool}.wdl"{as_alias}'.format(
                tools_dir=self.tools_dir if self.tools_dir else "",
                tool=self.name,
                as_alias=as_alias,
            )
