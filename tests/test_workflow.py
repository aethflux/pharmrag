import unittest

from agents.workflow import WORKFLOW_STEPS, build_langgraph_workflow


class WorkflowTests(unittest.TestCase):
    def test_workflow_steps_are_explicit(self) -> None:
        self.assertEqual(
            WORKFLOW_STEPS,
            [
                "risk_check",
                "attachment_extract",
                "retrieve",
                "answer",
                "citation_verify",
                "safety_postprocess",
                "log_metrics",
            ],
        )

    def test_langgraph_workflow_can_be_built_when_dependency_exists(self) -> None:
        workflow = build_langgraph_workflow()

        self.assertIsNotNone(workflow)


if __name__ == "__main__":
    unittest.main()
