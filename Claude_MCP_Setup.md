# Claude_MCP_Setup

## 1. What This Is
This guide sets up **PaddleOCR MCP** with **Claude Desktop** on Windows (Instructions Could Apply to MacOS) so Claude can OCR PDFs/images (including Arabic mode).

---

## 2. Prerequisites
1. Windows 10/11
2. Python 3.11 installed (`python --version` should show `3.11.x`)
3. Claude Desktop installed

---

## 3. Project Files You Need
Keep these in your project folder:
1. `app.py` (optional web demo)
2. `configs\paddleocr_mcp_ocr_mobile_fast.yaml`
3. `configs\paddleocr_mcp_ocr_arabic_fast.yaml`
4. `scripts\set-paddleocr-mode.ps1` (optional mode switch helper)



---


---

## 4. Install PaddleOCR MCP
```powershell
.\.paddle_mcp\Scripts\python.exe -m pip install "paddleocr-mcp[local-cpu]"
```
Note: You can also use it with GPU by adding this : "PADDLEOCR_MCP_DEVICE": "gpu:0" to the env


---



## 5. Configure Claude Desktop MCP
Claude Desktop config path:
`C:\Users\<YourUser>\AppData\Roaming\Claude\claude_desktop_config.json`

Use this JSON (replace `C:\Users\YourUser\Project_Folder` with your actual path):

```json
{
  "preferences": {
    "sidebarMode": "chat",
    "coworkScheduledTasksEnabled": false
  },
  "mcpServers": {
    "paddleocr": {
      "command": "C:\\Users\\YourUser\\Project_Folder\\.paddle_mcp\\Scripts\\python.exe",
      "args": ["-m", "paddleocr_mcp"],
      "env": {
        "PADDLEOCR_MCP_PIPELINE": "OCR",
        "PADDLEOCR_MCP_PPOCR_SOURCE": "local",
        "PADDLEOCR_MCP_PIPELINE_CONFIG": "C:\\Users\\YourUser\\Project_Folder\\configs\\paddleocr_mcp_ocr_arabic_fast.yaml",
        "PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT": "False",
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True",
        "FASTMCP_SHOW_CLI_BANNER": "false",
        "FASTMCP_CHECK_FOR_UPDATES": "off",
        "PYTHONWARNINGS": "ignore"
      }
    }
  }
}
```

Important:
1. Save as valid JSON
2. Save as **UTF-8 without BOM** (BOM can break Claude parsing)

---

## 6. Restart Claude Desktop
1. Fully close Claude Desktop
2. Reopen Claude Desktop

Claude only reloads MCP servers after restart.

---

## 7. Test in Claude
Use this exact prompt:

```text
Use MCP server "paddleocr" and tool "ocr" with:
{"input_data":"C:\\path\\to\\your.pdf","output_mode":"detailed"}

Return extracted text only.
Do not use fallback OCR tools.
If this MCP call fails, return the exact raw error.
```

---

## 8. Switch OCR Mode (Arabic vs General)

### Option A: Manual
Change this env value in `claude_desktop_config.json`:

1. Arabic-focused:
`configs\\paddleocr_mcp_ocr_arabic_fast.yaml`
2. General/mixed faster:
`configs\\paddleocr_mcp_ocr_mobile_fast.yaml`

Then restart Claude Desktop.

### Option B: Script
If using included script (update paths inside if needed):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\set-paddleocr-mode.ps1 -Mode arabic
powershell -ExecutionPolicy Bypass -File .\scripts\set-paddleocr-mode.ps1 -Mode general
```

Restart Claude after each switch.

---

## 9. Common Errors and Fixes

### Error: `Could not load app settings` / invalid JSON
Cause: bad JSON format or BOM encoding.
Fix:
1. Validate JSON structure
2. Save as UTF-8 **without BOM**

### Error: tool not found (`mcp_paddleocr_...`)
Cause: server name mismatch or Claude not restarted.
Fix:
1. Ensure server key is exactly `"paddleocr"`
2. Restart Claude Desktop fully

### OCR call fails with oneDNN / MKLDNN runtime errors
Fix: ensure env has:
`"PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT": "False"`

### Slow first run
Cause: model download.
Fix: wait for initial download; next runs are faster.

---

