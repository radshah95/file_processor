# 📄 File Processor API

Flexibly extract structured data from PDFs, Office documents, images and more, powered by Azure OpenAI and Docling.

---

## Table of contents
1.  Features
2.  Quick start
    • Prerequisites
    • Local run
    • Docker run
3.  Configuration (.env)
4.  API reference
    • `GET /` – health/debug
    • `POST /processFile` – extract data
5.  Example request & response
6.  Schema definition format
7.  Project layout
8.  Troubleshooting & tips
9.  Contributing
10. License
11. Assumptions
12. Improvements / Road-map

---

## 1. Features

• Accepts any file supported by [Docling](https://pypi.org/project/docling/) (currently PDF tested) \n
• Transforms the document to HTML, then asks Azure OpenAI to return only the fields you need. \n
• Fully async (Quart + Hypercorn).\n
• Stateless micro-service—ideal for serverless or container deployment. \n
• One-shot JSON schema: you choose which columns come back. \n

---

## 2. Quick start

### Prerequisites
* Python 3.12 + (or Docker)
* An Azure OpenAI resource and model deployment (`gpt-4o-mini` / `gpt-4o`, `gpt-4.1-mini`, etc.)
* An Azure Storage account only if Docling needs remote blobs (optional).

### Local run

```bash
git clone https://github.com/<you>/file_processor.git
cd file_processor

python -m venv .venv         # optional but recommended
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env         # create your secrets file (see §3)

python main.py               # server listens on http://localhost:5100
```

### Docker run

```bash
docker build -t file_processor:latest .
docker run --env-file .env -p 5100:5100 file_processor:latest
```

---

## 3. Configuration – `.env`

```ini
AZURE_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_API_KEY=<your-api-key>
AZURE_API_VERSION=2024-02-15-preview
```

Add any other env vars you need; the root (`GET /`) endpoint simply echoes them so you can verify container injection.

---

## 4. API reference

### 4.1 GET `/`
Health/debug. Returns current environment variables (HTML). Not intended for production.

### 4.2 POST `/processFile`
Extracts structured data according to a user-supplied schema.

• Content-Type: `multipart/form-data`
• Body parts
  • `file` – the document
  • `schema` – JSON text defining expected columns (see §6)

• Success response: `200 OK` + JSON object produced by the LLM.
• Error response: `500` + `{ "Error": ..., "Debug": ... }`

---

## 5. Example

```bash
curl -X POST http://localhost:5100/processFile \
  -F "file=@my_statement.pdf" \
  -F "schema=$(cat sample_schemas/schema1.json)"
```

Response:

```json
{
  "values": [
    {
      "Date": "2025-04-30",
      "Type": "Buy",
      "Ticker": "AAPL",
      "Quantity": 50,
      "Price": 165.42,
      "Cost_Basis": 8271.00,
      "Proceeds": 0,
      "Gain_Loss": -123.45
    }
  ]
}
```

---

## 6. Schema definition format

`schema` must be a JSON array where each element describes a desired column:

```json
[
  { "name": "Date",       "type": "string",  "desc": "YYYY-MM-DD" },
  { "name": "Quantity",   "type": "number",  "desc": "Number bought" },
  { "name": "Gain_Loss",  "type": "number",  "desc": "Net difference" }
]
```

Supported primitive types map to JSON Schema types (`string`, `number`, `integer`, `boolean`).
The backend converts this to the OpenAI function-calling / JSON-mode schema automatically; you don’t need to know that detail.

---

## 7. Project layout

```
.
├── api_blueprints/                # Quart blueprints
│   └── file_processing.py
├── api_functions/
│   └── process_file.py            # File → HTML → LLM → JSON
├── sample_schemas/                # Ready-to-use examples
├── main.py                        # Hypercorn entry-point
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 8. Troubleshooting & tips
* “Invalid response from model” – ensure the deployment name in `call_model()` matches what is deployed in Azure.
* Large files: Azure OpenAI currently limits prompt tokens. Consider pre-processing or splitting pages.
* GPU OCR: Docling automatically falls back to CPU if no GPU is available.
* Windows file handles: the backend writes to `tmp/`; make sure the directory exists and the process has permission.

---

## 9. Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

1. Fork the project
2. Create your feature branch: `git checkout -b feat/amazing`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feat/amazing`
5. Open a PR

---

## 10. License
This project is licensed under the MIT License – see LICENSE for details.

Happy parsing! ü•≥

---

## 11. Assumptions

The current implementation intentionally keeps the service surface small and opinionated.
Key assumptions baked into the design are:

• PDF ONLY - PDF is the **only** file type guaranteed to work end-to-end; it is assumed the input file is a PDF. I do not check for this right now so it will just error out.\n
• LARGE FILE = LONGER PROCESS TIME -The larger the file, the longer the call will take. Average PDF of 10 mb is already taking 1 - 1.5 minutes to process. Assume the call has a timeout set of > 10 minutes\n
• MODEL CONTEXT LIMIT -`DocumentConverter.convert()` always emits well-formed HTML that fits within the prompt window of the configured Azure OpenAI model. It is assumed right now that the content ouput will fit the context window of the available model.\n
• AZURE OPEN AI ONLY - An Azure OpenAI deployment with function-calling / JSON-mode support is available (e.g. `gpt-4o-mini`, `gpt-4.1-mini`). The model must support structured output. Right now there is only support of Azure OpenAI models.\n
• VALID JSON SCHEMA - The schema supplied by the caller is valid JSON and every `type` field maps through `_TYPE_MAP`.\n
• ONE CALL, ONE FILE - One request = one file. No batching or page-splitting logic exists at the API level. But because this is a basic endpoint, additional code can be built around to handle other use cases.\n
• TMP STORAGE REQUIRED - The service is stateless; temporary artefacts are written to `tmp/` and removed immediately after use. Docling requires a physical file to be written to drive to be processed (or a url somewhere)\n
• SECURITY IS AFTERTHOUGHT - Security is not a concern right now. There is no built-in server-side authentication or safety measures.\n

---

## 12. Improvements / Road-map

Planned or desirable upgrades:

1. **Multi-format support** – Enable and test Word, PowerPoint, image and email ingestion paths already available in Docling. Need to write the code to support multiple file types.
2. **Multiple File Conversion Options/Endponts** - Integrate more libraries as backup/secondary options of file processing like MarkerPDF or ImageMagick
2. **Multiple model support** - Include a proxy library like LiteLLM to make the solution model agnostic (as long as the model supports structured output, it can work).
3. **Large-document handling** – Add automatic chunking / windowing to stay within Azure OpenAI token limits, then merge partial JSON responses.
4. **Schema validation & feedback** – Return clear errors if the provided schema is invalid (unsupported type, missing fields, etc.).
5. **Streaming output** – Stream the LLM response (`text/event-stream`) for faster perceived latency on big documents.
6. **Offline batch processing** - If not streaming, at least offload the request to a offline pipeline that can take longer to process larger documents and then notify users of available output. We are hitting the upper limits of what is considered acceptable from a REST API response time
7. **Server-side Authentication & quota management** – API-key header, JWT or OAuth flow plus rate-limiting middleware.
8. **Observability** – Structured logging (JSON), request/response metrics and OpenTelemetry traces.
9. **Testing** – Use `pytest` + async test client to cover routes and model calls with fixtures/mocks.
10. **Retry / back-off strategy for Azure** – Gracefully recover from transient 502/429 errors with exponential back-off.
11. **Better Configurable tmp storage** – Allow an external volume or in-memory FS (e.g. `/dev/shm`) for faster I/O and better security. Lever cloud storage like S3.

Community PRs for any of the above are most welcome! 🚀