import yaml
from jsonschema import validate
from .models import Step, Workflow

SCHEMA = {
    "type": "object", "required": ["steps", "contract"],
    "properties": {
        "steps": {"type": "array", "items": {"type": "object", "required": ["id", "tool", "inputs", "expected_output", "needs_approval"]}},
        "contract": {"type": "array", "items": {"type": "string"}},
    },
}

def compile_workflow(text: str) -> tuple[Workflow, str]:
    data = yaml.safe_load(text)
    validate(data, SCHEMA)
    workflow = Workflow(
        steps=[Step(**item) for item in data["steps"]],
        contract=data["contract"],
    )
    return workflow, yaml.safe_dump(data, sort_keys=False)

