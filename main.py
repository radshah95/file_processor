import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from quart import Quart
from quart_cors import cors
from api_blueprints.file_processing import file_processing

app = Quart(__name__)
app = cors(app, allow_origin="*")

app.register_blueprint(file_processing)

if __name__ == "__main__":
    config = Config()
    config.bind = ["0.0.0.0:5100"]
    asyncio.run(serve(app, config))
