"""Stable diagnostics shared by command and application code."""


class AstreaError(Exception):
    def __init__(self, code, message, field=None, limit=None, exit_code=2):
        super().__init__(message)
        self.code = code
        self.field = field
        self.limit = limit
        self.exit_code = exit_code

    def diagnostic(self):
        result = {"code": self.code, "message": str(self)}
        if self.field is not None:
            result["field"] = self.field
        if self.limit is not None:
            result["limit"] = self.limit
        return result
