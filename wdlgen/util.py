from abc import ABC, abstractmethod
import json


def convert_python_value_to_wdl_literal(val) -> str:
    if val is None:
        # there is no NULL value yet
        return ""
    if hasattr(val, "get_string"):
        return val.get_string()
    if isinstance(val, dict):
        return ParameterMeta.ParamMetaAttribute(**val).get_string()

    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        # sanitise string here
        sanitised = val\
            .replace("\\", "\\\\")\
            .replace("\n", "\\n")\
            .replace('"', '\\"')
        return f'"{sanitised}"'

    return str(val)


class WdlBase(ABC):
    @abstractmethod
    def get_string(self):
        raise Exception("Subclass must override .get_string() method")


class KvClass(WdlBase):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_string(self, indent=0):
        l = []
        sorted_keys = sorted(self.kwargs.keys())
        for k in sorted_keys:
            val = self.kwargs[k]
            if val is None:
                continue

            if hasattr(val, "get_string"):
                val = val.get_string()

            l.append(indent * "  " + "{k}: {v}".format(k=k, v=val))
        return "\n".join(l)

    def __setitem__(self, key, value):
        self.kwargs[key] = value

    def __getitem__(self, item):
        return self.kwargs[item]


class WrappedKvClass(KvClass):
    def get_string(self, indent=0):
        l = []
        for k, v in self.kwargs.items():
            val = convert_python_value_to_wdl_literal(v)
            l.append("  " * indent + "{k}: {v}".format(k=k, v=val))
        return "\n".join(l)


class Meta(WrappedKvClass):
    def __init__(self, author=None, email=None, **kwargs):
        if author is not None:
            kwargs["author"] = author
        if email is not None:
            kwargs["email"] = email
        super().__init__(**kwargs)

    def add_author(self, author):
        self.kwargs["author"] = author

    def add_email(self, email):
        self.kwargs["email"] = email


class ParameterMeta(WrappedKvClass):
    class ParamMetaAttribute(KvClass):
        def __init__(self, help=None, suggestions=None, **kwargs):
            super().__init__(**kwargs)
            if help is not None:
                self.kwargs["help"] = help
            if suggestions is not None:
                self.kwargs["suggestions"] = suggestions

        def get_string(self, indent=0):
            l = []
            sorted_keys = sorted(self.kwargs.keys())
            for k in sorted_keys:
                v = self.kwargs[k]
                if v is None:
                    continue
                val = v
                if hasattr(v, "get_string"):
                    val = v.get_string()
                elif isinstance(v, dict):
                    val = ParameterMeta(**v).get_string(indent=indent)
                else:
                    val = convert_python_value_to_wdl_literal(val)

                l.append("{k}: {v}".format(k=k, v=val))
            return "{" + ", ".join(l) + "}"

        def __setitem__(self, key, value):
            self.kwargs[key] = value

        def __getitem__(self, item):
            return self.kwargs[item]
