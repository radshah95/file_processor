import os
from quart import Blueprint, request
from api_functions.process_file import process_file

file_processing = Blueprint("file_processing", __name__)


@file_processing.route("/", methods=["GET"])
async def API_index():
    os_env = []
    for name, value in os.environ.items():
        os_env.append(f"<p><strong>{name}:</strong> {value}</p>")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Processing API</title>
    </head>
    <body>
        <h1>Welcome to the file processor API</h1>
        <hr>
        <h2>OS Environment Variables:</h2>
        {"".join(os_env)}
    </body>
    </html>
    """


@file_processing.route("/processFile", methods=["POST"])
async def processFile():
    data = await request.form
    file_data = await request.files
    return await process_file(data, file_data)
