import httpx

try:
    from app.tools.base import ToolSpec
except Exception:
    try:
        from tools.base import ToolSpec
    except Exception:
        from .base import ToolSpec

class HttpTool(ToolSpec):
    
    def __init__(self):
        super().__init__()
        self.name = "http_tool"
        self.description = "Make HTTP calls: args (method, url, json, params)"

    def _run(self, method: str = "GET", url: str = "", json: dict | None = None, params: dict | None = None) -> str:
        if not url:
            return "Error: URL is required"
        
        try:
            with httpx.Client(timeout=10) as client:
                r = client.request(method=method, url=url, json=json, params=params)
                r.raise_for_status()
                
                try:
                    json_data = r.json()
                    return f"HTTP {r.status_code} Response (JSON):\n{json_data}"
                except Exception:
                    return f"HTTP {r.status_code} Response (Text):\n{r.text[:500]}{'...' if len(r.text) > 500 else ''}"
        except Exception as e:
            return f"HTTP Request Error: {str(e)}"
