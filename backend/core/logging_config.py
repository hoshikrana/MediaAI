import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, UTC
from contextvars import ContextVar
from uuid import uuid4

from backend.core.config import settings

# Context var for async-safe request ID tracking
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def get_request_id() -> str:
    return _request_id_var.get()

class MaskingFilter(logging.Filter):
    SENSITIVE_FIELDS = {"password", "token", "secret", "key", "authorization", "cookie", "api_key"}

    def filter(self, record: logging.LogRecord) -> bool:
        # Mask sensitive data in extra dict if present
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for k in record.extra.keys():
                if any(sens in k.lower() for sens in self.SENSITIVE_FIELDS):
                    record.extra[k] = "***MASKED***"
        return True

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "environment": settings.ENVIRONMENT
        }
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)[:500]
        
        # Merge extra fields
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                log_dict[key] = value

        return json.dumps(log_dict)

class ColoredConsoleFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m', 'INFO': '\033[92m', 'WARNING': '\033[93m', 
        'ERROR': '\033[91m', 'CRITICAL': '\033[95m'
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        req_id = get_request_id()
        req_str = f" [{req_id[:8]}]" if req_id else ""
        return f"{time_str} {color}[{record.levelname}]{self.RESET} {record.module}:{record.lineno}{req_str} — {record.getMessage()}"

def setup_logging():
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Clear existing handlers
    root_logger.handlers.clear()

    # Filters
    masking_filter = MaskingFilter()

    # Handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredConsoleFormatter() if not settings.is_production else JSONFormatter())
    console_handler.addFilter(masking_filter)

    app_file = RotatingFileHandler(settings.LOG_DIR / "app.log", maxBytes=10*1024*1024, backupCount=5)
    app_file.setFormatter(JSONFormatter())
    app_file.addFilter(masking_filter)

    err_file = RotatingFileHandler(settings.LOG_DIR / "error.log", maxBytes=10*1024*1024, backupCount=5)
    err_file.setLevel(logging.ERROR)
    err_file.setFormatter(JSONFormatter())
    err_file.addFilter(masking_filter)

    ml_file = RotatingFileHandler(settings.LOG_DIR / "ml.log", maxBytes=10*1024*1024, backupCount=5)
    ml_file.setFormatter(JSONFormatter())
    ml_file.addFilter(lambda r: "ml" in r.name)

    access_file = RotatingFileHandler(settings.LOG_DIR / "access.log", maxBytes=10*1024*1024, backupCount=5)
    access_file.setFormatter(JSONFormatter())
    access_file.addFilter(lambda r: "access" in r.name)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file)
    root_logger.addHandler(err_file)
    logging.getLogger("ml").addHandler(ml_file)
    logging.getLogger("access").addHandler(access_file)

    # Suppress noise
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

class MLLogger:
    def __init__(self):
        self.logger = logging.getLogger("ml")

    def log_model_load(self, name: str, device: str, load_time_ms: int, vram_delta_mb: int = None):
        self.logger.info("model_loaded", extra={
            "model_name": name, "device": device, "load_time_ms": load_time_ms, "vram_delta_mb": vram_delta_mb
        })

    def log_inference(self, name: str, inference_time_ms: int, input_summary: dict, output_summary: dict):
        self.logger.info("inference_complete", extra={
            "model_name": name, "inference_time_ms": inference_time_ms, "input": input_summary, "output": output_summary
        })

    def log_checkpoint(self, epoch: int, loss: float, val_loss: float, path: str):
        self.logger.info("checkpoint_saved", extra={"epoch": epoch, "loss": loss, "val_loss": val_loss, "path": path})

    def log_oom(self, model_name: str, batch_size: int, vram_available_mb: int):
        self.logger.error("cuda_oom", extra={"model_name": model_name, "batch_size": batch_size, "vram_available_mb": vram_available_mb})

    def log_pipeline_step(self, step_name: str, status: str, duration_ms: int, session_id: str):
        self.logger.info("pipeline_step", extra={"step": step_name, "status": status, "duration_ms": duration_ms, "session_id": session_id})

ml_logger = MLLogger()
