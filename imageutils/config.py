from typing import List
from pathlib import Path
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    custom_font_path: Path = Path("fonts")
    default_fallback_fonts: List[str] = [
        "Source Han Sans CN",
        "Arial",
        "Tahoma",
        "Segoe UI",
        "Microsoft YaHei",
        "Noto Sans SC",
        "Noto Sans CJK JP",
        "WenQuanYi Micro Hei",
        "Apple Color Emoji",
        "Noto Color Emoji",
        "Segoe UI Emoji",
        "Helvetica Neue",
        "Hiragino Sans GB",
        "PingFang SC",
        "Segoe UI Symbol",
    ]
