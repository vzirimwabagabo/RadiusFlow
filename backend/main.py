import logging

from fastapi import FastAPI
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from auth import get_current_user
from config import settings
from routers import auth as auth_routes
from routers import groups, logs, monitor, nas, sessions, sms, system, users

logger = logging.getLogger("radiusflow.api.main")

API_V1_PREFIX = settings.API_V1_PREFIX

app = FastAPI(
    title="RadiusFlow API",
    description="Enterprise Network Access Management API powered by FreeRADIUS",
    version="1.0.0",
    docs_url=None, # Disable default docs
    redoc_url=None  # Disable default redoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def register_api_routes(prefix: str = "", include_in_schema: bool = True) -> None:
    auth_dependencies = [Depends(get_current_user)]
    app.include_router(auth_routes.router, prefix=prefix, tags=["Auth"], include_in_schema=include_in_schema)
    app.include_router(users.router, prefix=prefix, tags=["Users"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(groups.router, prefix=prefix, tags=["Packages"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(nas.router, prefix=prefix, tags=["NAS"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(sessions.router, prefix=prefix, tags=["Sessions"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(monitor.router, prefix=prefix, tags=["Monitoring"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(logs.router, prefix=prefix, tags=["Logs"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(sms.router, prefix=prefix, tags=["Notifications"], dependencies=auth_dependencies, include_in_schema=include_in_schema)
    app.include_router(system.router, prefix=prefix, tags=["System"], include_in_schema=include_in_schema)


register_api_routes(API_V1_PREFIX)
register_api_routes(include_in_schema=False)


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "RadiusFlow API",
        "version": app.version,
        "docs": "/docs",
        "openapi": app.openapi_url,
        "api_prefix": API_V1_PREFIX,
    }

# --- MANDATORY CUSTOM SWAGGER UI OVERRIDES ---
CUSTOM_SWAGGER_CSS = """
/* Core Layout & Backgrounds */
body, .swagger-ui {
    background-color: #0b0f19 !important;
    color: #f3f4f6 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.swagger-ui .wrapper {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Top Header Bar */
.topbar {
    background-color: #111827 !important;
    border-bottom: 1px solid #1f2937 !important;
    padding: 10px 20px !important;
    display: flex !important;
    align-items: center !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
}
.topbar-wrapper {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}
/* Hide default Swagger logo */
.topbar-wrapper a {
    display: none !important;
}
/* Custom Branding Logo/Text */
.topbar-wrapper::after {
    content: "RadiusFlow API";
    color: #10b981;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-left: 10px;
}

/* Containers & Blocks */
.swagger-ui .scheme-container {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    margin-bottom: 20px !important;
    padding: 10px 20px !important;
}
.opblock {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 8px !important;
    margin-bottom: 10px !important;
    box-shadow: none !important;
}
.opblock.opblock-get .opblock-summary-method {
    background: #06b6d4 !important; /* Cyan for GET */
    border-radius: 4px 0 0 4px;
    color: #0b0f19 !important;
    font-weight: 700;
}
.opblock.opblock-post .opblock-summary-method {
    background: #10b981 !important; /* Emerald for POST */
    border-radius: 4px 0 0 4px;
    color: #0b0f19 !important;
    font-weight: 700;
}
.opblock.opblock-delete .opblock-summary-method {
    background: #ef4444 !important; /* Red for DELETE */
    border-radius: 4px 0 0 4px;
    color: white !important;
    font-weight: 700;
}

/* Text Elements & Headers */
.swagger-ui h1, .swagger-ui h2, .swagger-ui h3, .swagger-ui h4, .swagger-ui h5 {
    color: #f9fafb !important;
}
.swagger-ui .opblock .opblock-summary-path {
    color: #d1d5db !important;
    font-family: 'Fira Code', monospace !important;
}
.swagger-ui p, .swagger-ui span {
    color: #9ca3af !important;
}

/* Buttons & Execute Bars */
.btn.execute {
    background-color: #10b981 !important;
    border-color: #10b981 !important;
    color: #0b0f19 !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease;
}
.btn.execute:hover {
    background-color: #059669 !important;
}
.swagger-ui .btn.authorize {
    background-color: transparent !important;
    border: 1px solid #10b981 !important;
    color: #10b981 !important;
    border-radius: 6px !important;
}

/* Models & Response Bodies */
.swagger-ui .model-box {
    background: #0b0f19 !important;
    border: 1px solid #374151 !important;
    border-radius: 6px;
}
.swagger-ui .responses-inner {
    background: #0b0f19 !important;
}
.swagger-ui .response-col_status {
    color: #9ca3af !important;
}

/* Code/Syntax Highlighting (Dark Mode) */
.swagger-ui .highlight-code {
    background: #020617 !important;
    color: #e2e8f0 !important;
    border-radius: 6px;
    font-family: 'Fira Code', 'Courier New', monospace !important;
    font-size: 13px;
}
.swagger-ui .highlight-code .microlight {
    color: #e2e8f0 !important;
}

/* Inputs & Forms */
.swagger-ui input[type="text"], 
.swagger-ui input[type="password"], 
.swagger-ui textarea {
    background: #020617 !important;
    border: 1px solid #374151 !important;
    color: #f3f4f6 !important;
    border-radius: 6px !important;
}
.swagger-ui input[type="text"]:focus, 
.swagger-ui input[type="password"]:focus {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) !important;
}

/* Table Styling */
.swagger-ui table thead tr th {
    background: #111827 !important;
    color: #9ca3af !important;
    border-bottom: 1px solid #374151 !important;
}
.swagger-ui table tbody tr td {
    background: #0b0f19 !important;
    border-bottom: 1px solid #1f2937 !important;
}
/* Remove annoying lock icon background */
.swagger-ui .auth-container .unlocked {
    background: transparent !important;
}
"""

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{app.title} - Docs</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
            <link rel="icon" href="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f310.png">
            <style>{CUSTOM_SWAGGER_CSS}</style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {{
                    window.ui = SwaggerUIBundle({{
                        url: "{app.openapi_url}",
                        dom_id: "#swagger-ui",
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        layout: "StandaloneLayout"
                    }});
                }};
            </script>
        </body>
        </html>
        """
    )
