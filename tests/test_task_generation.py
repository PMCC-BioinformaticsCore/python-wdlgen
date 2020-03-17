import unittest

from wdlgen import (
    Input,
    Output,
    Workflow,
    Task,
    WdlType,
    String,
    WorkflowCall,
    WorkflowScatter,
    Meta,
    ParameterMeta,
)


class TestTaskGeneration(unittest.TestCase):

    def test_simple_task(self):
        # Task based on: https://github.com/openwdl/wdl/blob/master/versions/draft-2/SPEC.md#introduction
        t = Task("hello", runtime=Task.Runtime(docker="broadinstitute/my_image"))
        t.inputs.extend([
            Input(WdlType.parse_type("String"), "pattern"),
            Input(WdlType.parse_type("File"), "in")
        ])

        t.outputs.append(
            Output(WdlType.parse_type("Array[String]"), "matches", "read_lines(stdout())")
        )

        t.command = Task.Command("egrep", inputs=[Task.Command.CommandInput.from_input(i) for i in t.inputs])

        print(t.get_string())
        return t

    def test_readme(self):
        w = Workflow("workflow_name")

        w.imports.append(Workflow.WorkflowImport("tool_file", ""))
        w.inputs.append(Input(WdlType.parse_type("String"), "inputGreeting"))

        inputs_map = {"taskGreeting": "inputGreeting"}
        w.calls.append(WorkflowCall("Q.namspaced_task_identifier", "task_alias", inputs_map))
        w.outputs.append(Output(WdlType.parse_type("File"), "standardOut", "task_alias.standardOut"))

        print(w.get_string())

    def test_readme_task(self):
        t = Task("task_name")
        t.inputs.append(Input(WdlType.parse_type("String"), "taskGreeting"))
        # command in next section
        t.outputs.append(Output(WdlType.parse_type("File"), "standardOut", "stdout()"))

        command = Task.Command("echo")
        command.inputs.append(
            Task.Command.CommandInput("taskGreeting", optional=False, position=None, prefix="-a",
                                             separate_value_from_prefix=True, default=None))
        command.inputs.append(
            Task.Command.CommandInput("otherInput", optional=True, position=2, prefix="optional-param=",
                                             separate_value_from_prefix=False, default=None))
        command = Task.Command("echo")
        command.inputs.append(
            Task.Command.CommandInput("taskGreeting", optional=False, position=None, prefix="-a",
                                      separate_value_from_prefix=True, default=None))
        command.inputs.append(
            Task.Command.CommandInput("otherInput", optional=True, position=2, prefix="optional-param=",
                                      separate_value_from_prefix=False, default=None))

        # t is the task
        t.command = command
        print(t.get_string())


    @staticmethod
    def test_hello_tasks():
        # https://github.com/openwdl/wdl/#specifying-inputs-and-using-declarations

        t1 = Task("hello",
                  inputs=[Input(String, "name"), Input(String, "salutation")],
                  outputs=[Output(String, "response", "read_string(stdout())")]
                  )
        t1.command = Task.Command("echo",
                                  inputs=[Task.Command.CommandInput.from_input(t1.inputs[i], position=i) for i in
                                          range(2)])

        print(t1.get_string())

        return t1


class TestCommandGeneration(unittest.TestCase):
    def test_simple_command(self):
        command = Task.Command("egrep")
        command.inputs.append(Task.Command.CommandInput("pattern"))
        command.inputs.append(Task.Command.CommandInput("in"))

        expected = """\
egrep \\
  ~{pattern} \\
  ~{in}"""

        self.assertEqual(expected, command.get_string(0))

    def test_readme_example(self):
        command = Task.Command("echo")
        command.inputs.append(
            Task.Command.CommandInput(
                "taskGreeting",
                optional=False,
                position=None,
                prefix="-a",
                separate_value_from_prefix=True,
                default=None,
            )
        )
        command.inputs.append(
            Task.Command.CommandInput(
                "otherInput",
                optional=True,
                position=2,
                prefix="optional-param=",
                separate_value_from_prefix=False,
                default=None,
            )
        )
        expected = """\
echo \\
  -a ~{taskGreeting} \\
  ~{if defined(otherInput) then ('"' + "optional-param=" + otherInput + '"') else ""}"""
        # t is the task
        self.assertEqual(expected, command.get_string())

    def test_commandinput_space(self):
        t = Task.Command.CommandInput("taskGreeting", optional=False, position=None, prefix="-a",
                                      separate_value_from_prefix=True, default=None)
        self.assertEqual("-a ~{taskGreeting}", t.get_string())

    def test_commandinput_nospace(self):
        t = Task.Command.CommandInput("taskGreeting", optional=False, position=None, prefix="val=",
                                      separate_value_from_prefix=False, default=None)
        self.assertEqual("val=~{taskGreeting}", t.get_string())

    def test_commandarg_space(self):
        t = Task.Command.CommandInput("argVal", position=None, prefix="-p", separate_value_from_prefix=True)
        self.assertEqual("-p ~{argVal}", t.get_string())

    def test_commandarg_nospace(self):
        t = Task.Command.CommandArgument(prefix="arg=", value="argVal", position=None, separate_value_from_prefix=False)
        self.assertEqual("arg=argVal", t.get_string())


class TestWorkflowGeneration(unittest.TestCase):
    def test_hello_workflow(self):
        # https://github.com/openwdl/wdl/#specifying-inputs-and-using-declarations
        w = Workflow("test")

        w.calls.append(WorkflowCall(
            TestTaskGeneration.test_hello_tasks().name
        ))

        w.calls.append(WorkflowCall(
            TestTaskGeneration.test_hello_tasks().name,
            alias="hello2",
            inputs_map={
                "salutation": '"Greetings"',
                "name": '"Michael"'
            }
        ))

        print(w.get_string())


class TestWorkflowScatter(unittest.TestCase):
    def test_call_scatter(self):
        sc = WorkflowScatter("i", "integers", [
            WorkflowCall(Task("task1").name, inputs_map={"num": "i"}),
            WorkflowCall(Task("task2").name, inputs_map={"num": "task1.output"})
        ])

        print(sc.get_string(indent=0))
        print(sc.get_string(indent=1))
        print(sc.get_string(indent=2))


class TestWorkflowParameterMetaGeneration(unittest.TestCase):
    def test_parameter_meta_scalar(self):
        w = Task("param_meta_scalar", parameter_meta=ParameterMeta(test=42))

        expected = """\
task param_meta_scalar {
  parameter_meta {
    test: 42
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_parameter_meta_string(self):
        w = Task(
            "param_meta_string", parameter_meta=ParameterMeta(other="string value")
        )

        expected = """\
task param_meta_string {
  parameter_meta {
    other: "string value"
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_parameter_meta_obj(self):
        w = Task(
            "param_meta_obj",
            parameter_meta=ParameterMeta(
                obj_value=ParameterMeta.ParamMetaAttribute(
                    help="This is help text", scalar=96
                )
            ),
        )

        expected = """\
task param_meta_obj {
  parameter_meta {
    obj_value: "{"scalar": 96, "help": "This is help text"}"
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)


class TestWorkflowMetaGeneration(unittest.TestCase):
    def test_meta_scalar(self):
        w = Task("meta_scalar", meta=Meta(arbitrary_scalar=42))

        expected = """\
task meta_scalar {
  meta {
    arbitrary_scalar: 42
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)

    def test_meta_string(self):
        w = Task("meta_string", meta=Meta(author="illusional"))

        expected = """\
task meta_string {
  meta {
    author: "illusional"
  }
}"""
        derived_workflow_only = "".join(w.get_string().splitlines(keepends=True)[2:])
        self.assertEqual(expected, derived_workflow_only)
