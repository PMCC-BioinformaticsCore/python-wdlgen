
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional

from .util import WdlBase



@dataclass
class StepValueLine:
    tag: str
    value: str
    position: int = 999
    special: Optional[str] = None
    prefix: Optional[str] = None
    default: Optional[str] = None
    datatype: Optional[str] = None

    @property
    def tag_and_value(self) -> str:
        return f'{self.tag}={self.value}'

    
class StepValueSection:
    def __init__(self, lines: list[StepValueLine]):
        self.lines = self.order_lines(lines)
        self.padding = 2

    def order_lines(self, lines: list[StepValueLine]) -> list[StepValueLine]:
        lines.sort(key=lambda x: x.position)                    # normal position
        lines.sort(key=lambda x: x.special != '', reverse=True) # 'special' priority
        return lines

    @property
    def tag_value_width(self) -> int:
        width = max([len(f'{x.tag_and_value},') for x in self.lines])
        return self.add_padding(width)

    @property
    def datatype_width(self) -> int:
        lines = [x for x in self.lines if x.datatype is not None]
        if not lines:
            return 0
        width = max([len(x.datatype) for x in lines]) # type: ignore
        return self.add_padding(width)
    
    @property
    def prefix_width(self) -> int:
        lines = [x for x in self.lines if x.prefix is not None]
        if not lines:
            return 0
        width = max([len(x.prefix) for x in lines]) # type: ignore
        return self.add_padding(width)
    
    def add_padding(self, width: int) -> int:
        if width > 0:
            width += self.padding
        return width

    def render(self, indent: int, tb: str, render_comments: bool=True) -> str:
        str_lines: list[str] = []
        ind = (indent + 1) * tb
        
        # generate string representation of each line
        for i, ln in enumerate(self.lines):
            comma = ',' if i < len(self.lines) - 1 else ''   # ignore comma for last line
            datatype = f'{ln.datatype:<{self.datatype_width}}' if ln.datatype else ''
            prefix = f'{ln.prefix:<{self.prefix_width}}' if ln.prefix else ''
            default = ln.default if ln.default else ''
            special = ln.special if ln.special else ''
            
            if render_comments:
                tag_value = f'{ln.tag_and_value + comma:<{self.tag_value_width}}'
                str_line = f'{ind}{tb}{tag_value}# {datatype}{prefix}{default}  {special}'
            else:
                tag_value = f'{ln.tag_and_value + comma}'
                str_line = f'{ind}{tb}{tag_value}'
            str_lines.append(str_line)
        
        # join lines and return body segment
        inputs = '\n'.join(str_lines)
        return f"{{\n{ind}input:\n{inputs}"


class WorkflowCallBase(WdlBase, ABC):
    @abstractmethod
    def get_string(self, indent: int=1):
        raise Exception("Must override 'get_string(indent:int)'")


class WorkflowCall(WorkflowCallBase):

    def __init__(
        self,
        namespaced_identifier: str,
        alias: Optional[str] = None,
        inputs_details: dict[str, dict[str, Any]] = {},
        messages: Optional[list[str]] = None,
        render_comments: bool = True
    ):
        """
        would prefer the 'inputs_details' to be an object, but 
        don't want to have a shared dependency between janis-core and wdlgen.
        """
        """
        :param task:
        :param namespaced_identifier: Required if task is imported. The workflow might take care of this later?
        :param alias:
        :param inputs_details:
        """
        self.namespaced_identifier = namespaced_identifier
        self.alias = alias
        self.inputs_details = inputs_details
        self.messages: list[str] = messages if messages else []
        self.render_comments = render_comments

    def get_string(self, indent: int=1):
        self.tb: str = '  '
        self.indent: int = indent
        ind = self.indent * self.tb
        name = self.namespaced_identifier
        alias = ' as ' + self.alias if self.alias else ''
        body = self.get_body()
        msgs = '\n'.join([f'{ind}#{msg}' for msg in self.messages]) + '\n' if self.render_comments else ''
        return f'{msgs}{ind}call {name}{alias} {body}\n{ind}}}'

    def get_body(self) -> str:
        value_lines = self.init_known_input_lines()
        value_section = StepValueSection(value_lines)
        return value_section.render(indent=self.indent, tb=self.tb, render_comments=self.render_comments)

    def init_known_input_lines(self) -> list[StepValueLine]:
        out: list[StepValueLine] = []
        for tag, d in self.inputs_details.items():
            # init line
            line = StepValueLine(tag=tag, value=d['value'])
            # set optional info
            for key, val in d.items():
                if hasattr(line, key):
                    setattr(line, key, val)
            out.append(line)
        return out



class WorkflowConditional(WorkflowCallBase):
    def __init__(self, condition: str, calls: List[WorkflowCall] = None):
        self.condition = condition
        self.calls = calls or []

    def get_string(self, indent=1):
        body = "\n".join(c.get_string(indent=indent + 1) for c in self.calls)
        return "{ind}if ({condition}) {{\n {body}\n{ind}}}".format(
            ind=indent * "  ", condition=self.condition, body=body
        )


class WorkflowScatter(WorkflowCallBase):
    def __init__(
        self, identifier: str, expression: str, calls: List[WorkflowCall] = None
    ):
        self.identifier: str = identifier
        self.expression: str = expression
        self.calls: List[WorkflowCall] = calls if calls else []

    def get_string(self, indent=1):
        scatter_iteration_statement = "{identifier} in {expression}".format(
            identifier=self.identifier, expression=self.expression
        )

        body = "\n".join(c.get_string(indent=indent + 1) for c in self.calls)

        return "{ind}scatter ({st}) {{\n{body}\n{ind}}}".format(
            ind=indent * "  ", st=scatter_iteration_statement, body=body
        )
