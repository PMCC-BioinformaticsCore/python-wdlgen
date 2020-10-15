from typing import List, Any, Optional

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
        post_import_statements: Optional[List[WdlBase]] = None,
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

        self.post_import_statements = post_import_statements

        self.format = """
{pre}

workflow {name} {{
{blocks}
}}""".strip()

    def get_string(self, indent=0):
        tb = (indent + 1) * "  "

        name = self.name

        preblocks = []
        blocks = []

        if self.imports:
            preblocks.append(
                "\n".join(i.get_string(indent=indent) for i in self.imports)
            )

        if self.post_import_statements:
            base_tab = "  " * indent
            format_obj = (
                lambda pi: pi.get_string(indent=indent)
                if hasattr(pi, "get_string")
                else (base_tab + str(pi))
            )

            preblocks.append(
                "\n".join(format_obj(pi) for pi in self.post_import_statements)
            )

        if self.inputs:
            ins = []
            for i in self.inputs:
                wd = i.get_string(indent=indent + 1)
                if isinstance(wd, list):
                    ins.extend(wd)
                else:
                    ins.append(wd)
            blocks.append(f"{tb}input {{\n" + "\n".join(ins) + f"\n{tb}}}")

        if self.calls:
            base_tab = (indent + 1) * "  "
            format_obj = (
                lambda pi: pi.get_string(indent=indent+1)
                if hasattr(pi, "get_string")
                else (base_tab + str(pi))
            )
            blocks.append("\n".join(format_obj(c) for c in self.calls))

        if self.meta:
            mt = self.meta.get_string(indent=indent + 2)
            if mt:
                blocks.append("{tb}meta {{\n{args}\n{tb}}}".format(tb=tb, args=mt))

        if self.param_meta:
            pmt = self.param_meta.get_string(indent=2)
            if pmt:
                blocks.append(
                    "{tb}parameter_meta {{\n{args}\n{tb}}}".format(tb=tb, args=pmt)
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
            pre="\n\n".join(preblocks),
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

        def get_string(self, indent=0):
            tb = "  " * indent
            as_alias = " as " + self.alias if self.alias else ""
            return '{tb}import "{tools_dir}{tool}.wdl"{as_alias}'.format(
                tb=tb,
                tools_dir=self.tools_dir if self.tools_dir else "",
                tool=self.name,
                as_alias=as_alias,
            )
