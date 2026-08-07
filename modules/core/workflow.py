"""
Project : Blogger Download Auto Post V1.1
Module  : Workflow Controller
Version : 1.2.0

หน้าที่:

- ควบคุมขั้นตอนการทำงาน
- อ่านค่า workflow configuration
- เปิด/ปิดขั้นตอนตาม Config
- ตรวจสอบโหมดการทำงาน
- ควบคุมสิทธิ์ในการสร้างโพสต์
- รองรับ Publish / Schedule / Testing
"""


class WorkflowController:

    def __init__(
        self,
        workflow_config,
        logger=None
    ):

        self.workflow = (
            workflow_config
            if isinstance(workflow_config, dict)
            else {}
        )

        self.logger = logger


    # =========================================================
    # Logger
    # =========================================================

    def _log(
        self,
        level,
        message,
        data=None
    ):

        if not self.logger:
            return

        method = getattr(
            self.logger,
            level,
            None
        )

        if method:

            method(
                message,
                data
            )


    # =========================================================
    # Check Workflow Step
    # =========================================================

    def is_enabled(
        self,
        step
    ):

        steps = self.workflow.get(
            "steps",
            {}
        )


        enabled = bool(
            steps.get(
                step,
                False
            )
        )


        self._log(
            "info",
            "Workflow step checked",
            {
                "step": step,
                "enabled": enabled
            }
        )


        return enabled


    # =========================================================
    # Run Workflow Step
    # =========================================================

    def run_step(
        self,
        step_name,
        function,
        *args,
        **kwargs
    ):

        if not self.is_enabled(
            step_name
        ):

            self._log(
                "info",
                f"Skip step: {step_name}"
            )

            return None


        self._log(
            "info",
            f"Run step: {step_name}"
        )


        try:

            result = function(
                *args,
                **kwargs
            )


            self._log(
                "info",
                f"Step completed: {step_name}"
            )


            return result


        except Exception as error:

            self._log(
                "error",
                f"Step failed: {step_name}",
                {
                    "error_type": type(error).__name__,
                    "error": str(error)
                }
            )

            raise


    # =========================================================
    # Get Workflow Mode
    # =========================================================

    def get_mode(self):

        mode = self.workflow.get(
            "mode",
            "production"
        )


        if not isinstance(
            mode,
            str
        ):

            mode = "production"


        mode = mode.strip().lower()


        self._log(
            "info",
            "Workflow mode detected",
            {
                "mode": mode
            }
        )


        return mode


    # =========================================================
    # Testing Publish Permission
    # =========================================================

    def _allow_testing_publish(self):

        testing = self.workflow.get(
            "testing",
            {}
        )


        if not isinstance(
            testing,
            dict
        ):

            testing = {}


        allowed = bool(
            testing.get(
                "publish",
                False
            )
        )


        self._log(
            "info",
            "Testing publish permission checked",
            {
                "allowed": allowed
            }
        )


        return allowed


    # =========================================================
    # Publish / Schedule Permission
    # =========================================================

    def allow_publish(self):

        mode = self.get_mode()


        # -----------------------------------------------------
        # Testing
        # -----------------------------------------------------

        if mode == "testing":

            allowed = (
                self._allow_testing_publish()
            )


            self._log(
                "info",
                "Publish permission resolved",
                {
                    "mode": mode,
                    "allowed": allowed
                }
            )


            return allowed


        # -----------------------------------------------------
        # Production / Schedule
        #
        # main.py เรียก publisher.publish()
        # และ publisher.py จะเป็นตัวกำหนดว่า
        # โพสต์ถูกตั้งเวลาอย่างไร
        # -----------------------------------------------------

        if mode in (
            "production",
            "schedule"
        ):

            allowed = self.is_enabled(
                "publish"
            )


            self._log(
                "info",
                "Publish/Schedule permission resolved",
                {
                    "mode": mode,
                    "allowed": allowed
                }
            )


            return allowed


        # -----------------------------------------------------
        # Unknown mode
        #
        # ป้องกันไม่ให้ mode ที่ไม่รู้จัก
        # ไป Publish โดยไม่ตั้งใจ
        # -----------------------------------------------------

        self._log(
            "warning",
            "Unknown workflow mode - publishing disabled",
            {
                "mode": mode
            }
        )


        return False
