from typing import List, Optional

from wdlgen import WdlBase, WdlType


class StructField(WdlBase):
    def __init__(self, type_: WdlType, name: str):
        self.type_ = type_
        self.name = name

    def get_string(self, indent=0):
        ind = indent * "  "
        return f"{ind}{self.type_.get_string()} {self.name}"


class Struct(WdlBase):
    def __init__(self, name: str, fields: Optional[List[StructField]] = None):
        self.name = name
        self.fields = fields or []

    def add_field(self, type_: WdlType, name: str):
        self.fields.append(StructField(type_, name))

    def get_string(self, indent=0):
        tb = indent * "  "
        fields = "\n".join((f.get_string(indent=indent + 1)) for f in self.fields)
        return f"""\
{tb}struct {self.name} {{
{fields}
{tb}}}"""
