import re
from datetime import date, datetime

_VAR = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

def render_template(text: str, ctx: dict) -> str:
    def _repl(m):
        key = m.group(1)
        val = ctx.get(key, "")
        if isinstance(val, (date, datetime)):
            return val.isoformat()
        return str(val)
    return _VAR.sub(_repl, text or "")
