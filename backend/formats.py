"""Response formats: turn plain dicts into GeoJSON and CSV."""
import csv
import io

# Spreadsheets treat cells starting with these as formulas (CSV injection).
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value):
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def to_csv(rows, columns):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe_row = {}
        for column, value in row.items():
            safe_row[column] = csv_safe(value)
        writer.writerow(safe_row)
    return buffer.getvalue()