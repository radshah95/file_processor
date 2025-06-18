from quart import make_response
import traceback
from docling.document_converter import DocumentConverter
import json
from typing import List, Dict
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ.get("AZURE_ENDPOINT"),
    api_key=os.environ.get("AZURE_API_KEY"),
    api_version=os.environ.get("AZURE_API_VERSION"),
)


async def call_model(model, messages, schema):
    res = client.beta.chat.completions.parse(
        model=model, messages=messages, response_format=schema
    )
    json_data = json.loads(res.choices[0].message.content)
    return json_data


_TYPE_MAP = {
    "string": "string",
    "str": "string",
    "integer": "integer",
    "int": "integer",
    "double": "number",
    "float": "number",
    "number": "number",
    "bool": "boolean",
    "boolean": "boolean",
}


async def _json_type(raw_type: str) -> str:
    return _TYPE_MAP.get(raw_type.lower(), "string")


async def build_skeletal_schema(
    fields: List[Dict[str, str]],
    *,
    outer_name: str = "schema",
    array_prop: str = "values",
    wrapper_type: str = "json_schema",
) -> Dict:
    inner_properties: Dict[str, Dict] = {}
    for fld in fields:
        name = fld["name"]
        inner_properties[name] = {
            "type": await _json_type(fld["type"]),
            "description": fld.get("desc", ""),
        }
    schema = {
        "type": wrapper_type,
        "json_schema": {
            "name": outer_name,
            "schema": {
                "type": "object",
                "properties": {
                    array_prop: {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": inner_properties,
                            "required": list(inner_properties.keys()),
                            "additionalProperties": False,
                        },
                    }
                },
                "required": [array_prop],
                "additionalProperties": False,
            },
        },
    }
    return schema


async def process_file(data, file_data):
    try:
        file = file_data["file"]
        filename = file.filename

        schema_structure = await build_skeletal_schema(json.loads(data["schema"]))

        tmp = f"tmp/{filename}"

        with open(tmp, "wb") as f:
            f.write(file.read())

        converter = DocumentConverter()

        result = converter.convert(tmp)

        os.remove(tmp)

        output = result.document.export_to_html()

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
                    Please extract key information from the following input based on the provided schema:
                    {output}
                    """,
                    },
                ],
            }
        ]

        structured_output = await call_model("gpt-4.1-mini", messages, schema_structure)

        return await make_response(
            structured_output,
            200,
        )
    except Exception as e:
        return await make_response(
            {"Error": str(e), "Debug": traceback.format_exc()}, 500
        )
