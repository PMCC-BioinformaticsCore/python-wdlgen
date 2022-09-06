from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import Any, List, Optional

from .util import WdlBase



@dataclass
class StepValueLine:
    tag: str
    value: Optional[str]
    special_label: Optional[str]
    prefix_label: Optional[str]
    default_label: Optional[str]
    #default_label: bool
    datatype_label: str 

    @cached_property
    def length(self) -> int:  
        return len(f'{self.tag_and_value},')
    
    @property
    def tag_and_value(self) -> str:
        return f'{self.tag}={self.value},'
    
    @property
    def info_comment(self) -> str:
        prefix = f' {self.prefix_label}' if self.prefix_label is not None else ''
        datatype = f' [{self.datatype_label}]' if self.datatype_label is not None else ''
        default = f' ({self.default_label})' if self.default_label is not None else ''
        special = f' **{self.special_label}' if self.special_label is not None else ''
        #default = f' (default)' if self.default_label is True else ''
        return f'#{special}{prefix}{datatype}{default}'



class WorkflowCallBase(WdlBase, ABC):
    @abstractmethod
    def get_string(self, indent: int=1):
        raise Exception("Must override 'get_string(indent:int)'")


class WorkflowCall(WorkflowCallBase):

    def __init__(
        self,
        namespaced_identifier: str,
        alias: str,
        inputs_details: dict[str, dict[str, Any]],
        messages: list[str],
        render_comments: bool = True
    ):
        """
        :param task:
        :param namespaced_identifier: Required if task is imported. The workflow might take care of this later?
        :param alias:
        :param inputs_details:
        """
        self.namespaced_identifier = namespaced_identifier
        self.alias = alias
        self.inputs_details = inputs_details
        self.messages = messages
        self.render_comments = render_comments

    def get_string(self, indent: int=1):
        self.tb: str = "  "
        self.indent: int = 1
        ind = self.indent * self.tb
        name = self.namespaced_identifier
        alias = " as " + self.alias if self.alias else ""  # alias is always being supplied, but this implies its not?
        body = self.get_body()
        return f"{ind}call {name}{alias} {body}\n{ind}}}"

    def get_body(self) -> str:
        lines = self.init_known_input_lines()
        return self.input_section_to_string(lines)

    def init_known_input_lines(self) -> list[StepValueLine]:
        out: list[StepValueLine] = []
        for tag, d in self.inputs_details.items():
            line = StepValueLine(
                tag=tag, 
                value=d['value'], 
                special_label=d['special_label'], 
                prefix_label=d['prefix'], 
                default_label=d['default'], 
                datatype_label=d['datatype']
            )
            out.append(line)
        return out
        
    def input_section_to_string(self, lines: list[StepValueLine]) -> str:
        str_lines: list[str] = []
        ind = (self.indent + 1) * self.tb

        # render 'unknown' input messages
        if self.render_comments:
            str_lines += [f'{ind}{self.tb}#{m},' for m in self.messages]
        
        # calc longest line so we know how to justify info comments
        max_line_len = max([ln.length for ln in lines])
        
        # generate string representaiton of each line
        for ln in lines:
            if self.render_comments:
                str_line = f'{ind}{self.tb}{ln.tag_and_value:<{max_line_len+2}}{ln.info_comment}'
            else:
                str_line = f'{ind}{self.tb}{ln.tag_and_value}'
            str_lines.append(str_line)
        
        # join lines and return body segment
        inputs = '\n'.join(str_lines)
        return f"{{\n{ind}input:\n{inputs}"



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

        return "{ind}scatter ({st}) {{\n {body}\n{ind}}}".format(
            ind=indent * "  ", st=scatter_iteration_statement, body=body
        )
