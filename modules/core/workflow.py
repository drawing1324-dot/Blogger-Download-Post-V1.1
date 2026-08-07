"""
Project : Blogger Download Auto Post V1.1
Module  : Workflow Controller
Version : 1.1.0

หน้าที่:
- ควบคุมขั้นตอนการทำงาน
- อ่านค่า workflow.json
- เปิด/ปิดขั้นตอนตาม Config
"""


class WorkflowController:


    def __init__(
        self,
        workflow_config,
        logger=None
    ):

        self.workflow = workflow_config

        self.logger = logger



    def is_enabled(
        self,
        step
    ):

        steps = (
            self.workflow
            .get("steps", {})
        )

        return steps.get(
            step,
            False
        )



    def run_step(
        self,
        step_name,
        function,
        *args,
        **kwargs
    ):

        if not self.is_enabled(step_name):

            if self.logger:

                self.logger.info(
                    f"Skip step: {step_name}"
                )

            return None


        if self.logger:

            self.logger.info(
                f"Run step: {step_name}"
            )


        result = function(
            *args,
            **kwargs
        )


        return result



    def get_mode(self):

        return (
            self.workflow
            .get(
                "mode",
                "production"
            )
        )



    def allow_publish(self):

        mode = self.get_mode()


        if mode == "testing":

            testing = (
                self.workflow
                .get(
                    "testing",
                    {}
                )
            )

            return testing.get(
                "publish",
                False
            )


        return self.is_enabled(
            "publish"
        )
