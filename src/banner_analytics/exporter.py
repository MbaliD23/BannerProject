from __future__ import annotations

from io import BytesIO

import pandas as pd

from .repository import EXPORT_COLUMNS


def _excel_safe_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return an export copy with Excel-compatible, Johannesburg-local datetimes."""
    exported = frame[columns].copy()
    for column in exported.columns:
        if isinstance(exported[column].dtype, pd.DatetimeTZDtype):
            exported[column] = (
                exported[column]
                .dt.tz_convert("Africa/Johannesburg")
                .dt.tz_localize(None)
            )
    return exported


def csv_bytes(frame: pd.DataFrame) -> bytes:
    columns = [column for column in EXPORT_COLUMNS if column in frame.columns]
    return frame[columns].to_csv(index=False).encode("utf-8-sig")


def excel_bytes(frame: pd.DataFrame) -> bytes:
    columns = [column for column in EXPORT_COLUMNS if column in frame.columns]
    exported = _excel_safe_frame(frame, columns)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        exported.to_excel(writer, sheet_name="Banner Analytics", index=False)
        sheet = writer.sheets["Banner Analytics"]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column) + 2, 55)
            sheet.column_dimensions[column[0].column_letter].width = width
    return output.getvalue()

