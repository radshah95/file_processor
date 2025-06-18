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

---

## 1. Features
• Accepts any file supported by [Docling](https://pypi.org/project/docling/) (PDF, DOCX, PPTX, XLSX, images, …).
• Transforms the document to HTML, then asks Azure OpenAI to return only the fields you need.
• Fully async (Quart + Hypercorn).
• Stateless micro-service—ideal for serverless or container deployment.
• One-shot JSON schema: you choose which columns come back.

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
&nbsp;&nbsp;• `file` – the document
&nbsp;&nbsp;• `schema` – JSON text defining expected columns (see §6)

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
    },
    ...
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

Supported primitive types are mapped to JSON Schema types (`string`, `number`, `integer`, `boolean`).

The backend converts this to the OpenAI function-calling/JSON Mode schema automatically; you don’t need to know that detail.

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

Happy parsing! 🥳