

``` python
import json
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

# NEEDS TO BE DONE LOCALLY, UPDATE PATH TO MATCH YOUR LOCAL SETUP
# From Quarto revision 71945532e1fc1a5cf113117f6d5ff5bee3991797
quarto_local_path = Path("~/work/quarto-dev/quarto-cli")
schema_path = quarto_local_path.expanduser().joinpath("src/resources/schema/json-schemas.json")

if not schema_path.exists():
    raise FileNotFoundError(f"Path {schema_path} does not exist")

with open(schema_path, 'r') as schema_file:
    schema = json.load(schema_file)
```

``` python
def validate_json_schema(schema):
    try:
        Draft202012Validator.check_schema(schema)
        print("Schema is valid according to JSON Schema 2020-12 specification.")
    except jsonschema.exceptions.SchemaError as e:
        print(f"Schema is invalid: {e}")
```

``` python
validate_json_schema(schema)
```

    Schema is invalid: {'values': ['plain', 'webtex', 'gladtex', 'mathml', 'mathjax', 'katex']} is not of type 'array'

    Failed validating 'type' in metaschema['allOf'][0]['properties']['$defs']['additionalProperties']['$dynamicRef']['allOf'][3]['properties']['enum']:
        {'type': 'array', 'items': True}

    On schema['$defs']['MathMethods']['enum']:
        {'values': ['plain', 'webtex', 'gladtex', 'mathml', 'mathjax', 'katex']}

``` python
schema["$defs"] = {k: v for k, v in schema["$defs"].items() if k.startswith("Brand")}
# not required but useful for brand-yaml work
# schema["type"] = "object"
# schema["properties"] = {"brand": {"$ref": "#/$defs/Brand"}}
schema["$ref"] = "#/$defs/Brand"

validate_json_schema(schema)
```

    Schema is valid according to JSON Schema 2020-12 specification.

<details>

<summary>

<code>brand-schema.json</code>
</summary>

``` python
import json
from pathlib import Path

with Path(".").joinpath("brand.schema.json").open("w") as f:
    f.write(json.dumps(schema, indent=2))

# print(json.dumps(schema, indent=2))
```

</details>
