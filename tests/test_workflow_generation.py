import unittest
from wdlgen import Workflow, Meta, ParameterMeta
from tests.helpers import non_blank_lines_list


class TestWorkflowParameterMetaGeneration(unittest.TestCase):
    def test_parameter_meta_scalar(self):
        wf = Workflow("param_meta_scalar", parameter_meta=ParameterMeta(test=42))
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow param_meta_scalar {
  parameter_meta {
    test: 42
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

    def test_parameter_meta_string(self):
        wf = Workflow(
            "param_meta_string", parameter_meta=ParameterMeta(other="string value")
        )
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow param_meta_string {
  parameter_meta {
    other: "string value"
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

    def test_parameter_meta_bool(self):
        wf = Workflow(
            "param_meta_scalar", parameter_meta=ParameterMeta(pos=True, neg=False)
        )
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow param_meta_scalar {
  parameter_meta {
    pos: true
    neg: false
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

    def test_parameter_meta_obj(self):
        wf = Workflow(
            "param_meta_obj",
            parameter_meta=ParameterMeta(
                obj_value=ParameterMeta.ParamMetaAttribute(
                    help="This is help text", scalar=96
                )
            ),
        )
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow param_meta_obj {
  parameter_meta {
    obj_value: {help: "This is help text", scalar: 96}
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

    def test_parameter_meta_dict(self):
        wf = Workflow(
            "param_meta_obj",
            parameter_meta=ParameterMeta(
                obj_value={
                    "help": "This is help text", "scalar": 96
                }
            ),
        )
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow param_meta_obj {
  parameter_meta {
    obj_value: {help: "This is help text", scalar: 96}
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

class TestWorkflowMetaGeneration(unittest.TestCase):
    def test_meta_scalar(self):
        wf = Workflow("meta_scalar", meta=Meta(arbitrary_scalar=42))
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow meta_scalar {
  meta {
    arbitrary_scalar: 42
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

    def test_meta_string(self):
        wf = Workflow("meta_string", meta=Meta(author="illusional"))
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow meta_string {
  meta {
    author: "illusional"
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)

    def test_meta_bool(self):
        wf = Workflow("meta_scalar", meta=Meta(pos=True, neg=False))
        wf_str = wf.get_string()
        wf_lines = non_blank_lines_list(wf_str)
        expected = """\
workflow meta_scalar {
  meta {
    pos: true
    neg: false
  }
}"""
        wf_str = '\n'.join(wf_lines[1:])
        self.assertEqual(expected, wf_str)
