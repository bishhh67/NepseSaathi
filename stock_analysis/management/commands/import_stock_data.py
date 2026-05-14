"""
Management command: import_stock_data
Usage:
    python manage.py import_stock_data /path/to/csv_folder

Each CSV file must be named after the stock symbol (e.g. NABIL.csv).
Expected columns (case-insensitive header matching):
    DATE  CHANGE  CHANGE %  CLOSE  TURNOVER  VOLUME  TRADE  OPEN  HIGH  LOW
"""

import os
import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from stock_analysis.models import StockDailyData


# ── helpers ───────────────────────────────────────────────────────────────

def _clean_float(value: str) -> float:
    """Remove commas, percent signs, spaces; return float. Return 0.0 on failure."""
    try:
        return float(value.replace(",", "").replace("%", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _clean_int(value: str) -> int:
    """Remove commas, spaces; return int. Return 0 on failure."""
    try:
        return int(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def _parse_date(value: str):
    """
    Try multiple date formats commonly found in NEPSE data exports.
    Returns a datetime.date object or None.
    """
    formats = [
        "%Y-%m-%d",   # 2024-01-15
        "%d-%m-%Y",   # 15-01-2024
        "%m/%d/%Y",   # 01/15/2024
        "%d/%m/%Y",   # 15/01/2024
        "%Y/%m/%d",   # 2024/01/15
        "%b %d, %Y",  # Jan 15, 2024
        "%d %b %Y",   # 15 Jan 2024
    ]
    value = value.strip()
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_header(header: str) -> str:
    """Lowercase and strip header for flexible matching."""
    return header.strip().lower().replace(" ", "").replace("%", "percent")


# Column name mapping: normalized header → model field name
COLUMN_MAP = {
    "date":          "date",
    "change":        "change",
    "changepercent": "change_percent",
    "close":         "close_price",
    "turnover":      "turnover",
    "volume":        "volume",
    "trade":         "trade_count",
    "trades":        "trade_count",
    "open":          "open_price",
    "high":          "high_price",
    "low":           "low_price",
}


class Command(BaseCommand):
    help = "Import NEPSE stock data from CSV files into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_folder",
            type=str,
            help="Path to the folder containing NEPSE CSV files.",
        )
        parser.add_argument(
            "--symbol",
            type=str,
            default=None,
            help="Import only a specific symbol (e.g. --symbol NABIL).",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            default=False,
            help="Update existing rows instead of skipping duplicates.",
        )

    def handle(self, *args, **options):
        folder    = options["csv_folder"]
        only_sym  = options["symbol"].upper() if options["symbol"] else None
        do_update = options["update"]

        if not os.path.isdir(folder):
            raise CommandError(f"Folder not found: {folder}")

        csv_files = [
            f for f in os.listdir(folder)
            if f.upper().endswith(".CSV")
        ]

        if not csv_files:
            raise CommandError(f"No CSV files found in: {folder}")

        total_created = 0
        total_updated = 0
        total_skipped = 0
        total_errors  = 0

        for filename in sorted(csv_files):
            symbol = os.path.splitext(filename)[0].upper().strip()

            if only_sym and symbol != only_sym:
                continue

            filepath = os.path.join(folder, filename)
            created, updated, skipped, errors = self._import_file(
                filepath, symbol, do_update
            )
            total_created += created
            total_updated += updated
            total_skipped += skipped
            total_errors  += errors

            self.stdout.write(
                f"  {symbol:12s} → created={created:4d}  "
                f"updated={updated:4d}  skipped={skipped:4d}  errors={errors:3d}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Total: created={total_created}  "
            f"updated={total_updated}  skipped={total_skipped}  errors={total_errors}"
        ))

    # ── private ──────────────────────────────────────────────────────────

    def _import_file(self, filepath: str, symbol: str, do_update: bool):
        created = updated = skipped = errors = 0

        try:
            with open(filepath, newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)

                # Build a normalized → original header map
                raw_headers = reader.fieldnames or []
                header_map  = {_normalize_header(h): h for h in raw_headers}

                rows_to_create = []
                rows_to_update = []

                for row_num, row in enumerate(reader, start=2):
                    try:
                        record = self._parse_row(row, header_map, symbol)
                        if record is None:
                            errors += 1
                            continue

                        if do_update:
                            rows_to_update.append(record)
                        else:
                            rows_to_create.append(record)

                    except Exception as exc:
                        self.stderr.write(
                            f"    Row {row_num} in {filepath}: {exc}"
                        )
                        errors += 1

                # Bulk create (ignore conflicts = skip duplicates)
                if rows_to_create:
                    objs = StockDailyData.objects.bulk_create(
                        [StockDailyData(**r) for r in rows_to_create],
                        update_conflicts=False,
                        ignore_conflicts=True,
                    )
                    # bulk_create with ignore_conflicts returns only inserted rows
                    created  = len(objs)
                    skipped  = len(rows_to_create) - created

                # Upsert one-by-one if --update
                if rows_to_update:
                    for record in rows_to_update:
                        obj, was_created = StockDailyData.objects.update_or_create(
                            symbol=record["symbol"],
                            date=record["date"],
                            defaults={k: v for k, v in record.items()
                                      if k not in ("symbol", "date")},
                        )
                        if was_created:
                            created += 1
                        else:
                            updated += 1

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  Failed to read {filepath}: {exc}"))
            errors += 1

        return created, updated, skipped, errors

    def _parse_row(self, row: dict, header_map: dict, symbol: str):
        """
        Map raw CSV row → dict ready for StockDailyData(**record).
        Returns None if essential fields are missing.
        """
        def get(norm_key):
            """Get raw string value by normalised key."""
            orig = header_map.get(norm_key)
            if orig is None:
                return ""
            return row.get(orig, "")

        # Date is essential
        raw_date = get("date")
        parsed_date = _parse_date(raw_date)
        if parsed_date is None:
            raise ValueError(f"Cannot parse date: '{raw_date}'")

        # Close is essential
        raw_close = get("close")
        if not raw_close.strip():
            raise ValueError("Empty close price")
        close = _clean_float(raw_close)

        return {
            "symbol":         symbol,
            "date":           parsed_date,
            "change":         _clean_float(get("change")),
            "change_percent": _clean_float(get("changepercent")),
            "close_price":    close,
            "turnover":       _clean_float(get("turnover")),
            "volume":         _clean_int(get("volume")),
            "trade_count":    _clean_int(get("trade") or get("trades")),
            "open_price":     _clean_float(get("open")),
            "high_price":     _clean_float(get("high")),
            "low_price":      _clean_float(get("low")),
        }