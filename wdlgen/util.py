from abc import ABC, abstractmethod
import json


class WdlBase(ABC):
    @abstractmethod
    def get_string(self):
        raise Exception("Subclass must override .get_string() method")


class KvClass(WdlBase):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_string(self):
        l = []
        for k, v in self.kwargs.items():
            val = v
            if hasattr(v, "get_string"):
                val = v.get_string()
            l.append("{k}: {v}".format(k=k, v=val))
        return l

    def __setitem__(self, key, value):
        self.kwargs[key] = value

    def __getitem__(self, item):
        return self.kwargs[item]


class WrappedKvClass(KvClass):
    def get_string(self):
        l = []
        for k, v in self.kwargs.items():
            val = v
            if hasattr(v, "get_string"):
                val = v.get_string()
            if isinstance(val, str):
                val = f'"{val}"'
            l.append("{k}: {v}".format(k=k, v=val))
        return l


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
    class ParamMetaAttribute(WdlBase):
        def __init__(self, help=None, suggestions=None, **kwargs):
            self.kwargs = kwargs
            if help is not None:
                self.kwargs["help"] = help
            if suggestions is not None:
                self.kwargs["suggestions"] = suggestions

        def get_string(self):
            return json.dumps(self.kwargs or {})

        def __setitem__(self, key, value):
            self.kwargs[key] = value

        def __getitem__(self, item):
            return self.kwargs[item]
