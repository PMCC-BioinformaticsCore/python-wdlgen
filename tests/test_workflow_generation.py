import unittest
from wdlgen import Workflow, Meta, ParameterMeta


class TestWorkflowParameterMetaGeneration(unittest.TestCase):
    def test_parameter_meta_scalar(self):
        w = Workflow("param_meta_scalar", parameter_meta=ParameterMeta(test=42))

        expected = """\
workflow param_meta_scalar {
  parameter_meta {
    test: 42
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_parameter_meta_string(self):
        w = Workflow(
            "param_meta_string", parameter_meta=ParameterMeta(other="string value")
        )

        expected = """\
workflow param_meta_string {
  parameter_meta {
    other: "string value"
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_parameter_meta_bool(self):
        w = Workflow(
            "param_meta_scalar", parameter_meta=ParameterMeta(pos=True, neg=False)
        )

        expected = """\
workflow param_meta_scalar {
  parameter_meta {
    pos: true
    neg: false
  }
}"""
        derived_task_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_task_only)

    def test_parameter_meta_obj(self):
        w = Workflow(
            "param_meta_obj",
            parameter_meta=ParameterMeta(
                obj_value=ParameterMeta.ParamMetaAttribute(
                    help="This is help text", scalar=96
                )
            ),
        )

        expected = """\
workflow param_meta_obj {
  parameter_meta {
    obj_value: {help: "This is help text", scalar: 96}
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_parameter_meta_dict(self):
        w = Workflow(
            "param_meta_obj",
            parameter_meta=ParameterMeta(
                obj_value={"help": "This is help text", "scalar": 96}
            ),
        )

        expected = """\
workflow param_meta_obj {
  parameter_meta {
    obj_value: {help: "This is help text", scalar: 96}
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)


class TestWorkflowMetaGeneration(unittest.TestCase):
    def test_meta_scalar(self):
        w = Workflow("meta_scalar", meta=Meta(arbitrary_scalar=42))

        expected = """\
workflow meta_scalar {
  meta {
    arbitrary_scalar: 42
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_meta_string(self):
        w = Workflow("meta_string", meta=Meta(author="illusional"))

        expected = """\
workflow meta_string {
  meta {
    author: "illusional"
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_meta_bool(self):
        w = Workflow("meta_scalar", meta=Meta(pos=True, neg=False))

        expected = """\
workflow meta_scalar {
  meta {
    pos: true
    neg: false
  }
}"""
        result = w.get_string()
        derived_task_only = "".join(result.splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_task_only)
