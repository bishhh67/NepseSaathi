"""
services/stock_explainer.py

Pure-Python stock movement analysis engine for NEPSE Sathi.
No pandas required — all calculations use standard Python.

Usage:
    from stock_analysis.services.stock_explainer import explain_stock_movement
    result = explain_stock_movement("NABIL", date(2024, 3, 15))
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from stock_analysis.models import StockDailyData


# ─────────────────────────────────────────────────────────────────────────────
# Data containers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PriceClassification:
    label: str          # e.g. "Strong Bullish"
    css_class: str      # tailwind colour hint consumed by template
    emoji: str


@dataclass
class VolumeSignal:
    label: str          # Normal / Elevated / High / Extreme
    ratio: float        # selected_vol / avg_20d_vol
    avg_20d: float
    css_class: str


@dataclass
class TrendSignal:
    label: str          # Bullish / Bearish / Sideways / Reversal
    ma5: Optional[float]
    ma20: Optional[float]
    css_class: str
    detail: str


@dataclass
class BreakoutSignal:
    breakout: bool
    breakdown: bool
    prev_20d_high: Optional[float]
    prev_20d_low: Optional[float]
    label: str
    css_class: str


@dataclass
class MomentumSignal:
    label: str          # Strong / Moderate / Weak / Negative
    intraday_range_pct: float   # (high - low) / open * 100
    close_vs_open_pct: float    # (close - open) / open * 100
    css_class: str


@dataclass
class AnalysisResult:
    # target row
    symbol: str
    target_date: date
    row: StockDailyData

    # signals
    price_class: PriceClassification
    volume: VolumeSignal
    trend: TrendSignal
    breakout: BreakoutSignal
    momentum: MomentumSignal

    # natural-language output
    primary_reason: str
    supporting_reasons: list[str] = field(default_factory=list)
    confidence_score: int = 0   # 0-100

    # history
    recent_history: list[StockDailyData] = field(default_factory=list)

    # meta
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_div(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    if denominator == 0:
        return fallback
    return numerator / denominator


def _moving_average(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _pct_change(new: float, old: float) -> float:
    if old == 0:
        return 0.0
    return round((new - old) / old * 100, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Classification functions
# ─────────────────────────────────────────────────────────────────────────────

def _classify_price(change_pct: float) -> PriceClassification:
    """
    Classify price movement based on change %.
    NEPSE circuit limit is ±10 %, so we calibrate accordingly.
    """
    if change_pct >= 5:
        return PriceClassification("Strong Bullish",  "green",  "🚀")
    if change_pct >= 2:
        return PriceClassification("Moderate Bullish","lime",   "📈")
    if change_pct >= -2:
        return PriceClassification("Neutral",         "gray",   "➡️")
    if change_pct >= -5:
        return PriceClassification("Moderate Bearish","orange", "📉")
    return PriceClassification("Strong Bearish",      "red",    "🔻")


def _classify_volume(
    selected_vol: int,
    prev_rows: list[StockDailyData],
) -> VolumeSignal:
    """Compare today's volume against 20-day average."""
    vols   = [r.volume for r in prev_rows if r.volume > 0]
    avg_20 = _moving_average(vols) or 1.0
    ratio  = round(_safe_div(selected_vol, avg_20), 2)

    if ratio >= 3.0:
        label, css = "Extreme",  "red"
    elif ratio >= 2.0:
        label, css = "High",     "orange"
    elif ratio >= 1.4:
        label, css = "Elevated", "yellow"
    else:
        label, css = "Normal",   "gray"

    return VolumeSignal(label=label, ratio=ratio, avg_20d=round(avg_20, 0), css_class=css)


def _classify_trend(
    target_close: float,
    prev_rows: list[StockDailyData],
) -> TrendSignal:
    """5-day and 20-day MA based trend detection."""
    closes = [r.close_price for r in prev_rows]   # ordered newest-first

    ma5  = _moving_average(closes[:5])
    ma20 = _moving_average(closes[:20])

    if ma5 is None:
        return TrendSignal("Insufficient Data", None, None, "gray", "Not enough history for trend analysis.")

    # Compare current close to MAs
    above_ma5  = target_close > ma5
    above_ma20 = ma20 is not None and target_close > ma20

    if ma20 is not None:
        if above_ma5 and above_ma20:
            if ma5 > ma20:
                label  = "Bullish"
                detail = f"Price is above both MA5 ({ma5}) and MA20 ({ma20}), with MA5 crossing above MA20."
                css    = "green"
            else:
                label  = "Trend Reversal (Bullish)"
                detail = f"Price broke above MA5 ({ma5}) but MA20 ({ma20}) still above — early reversal signal."
                css    = "lime"
        elif not above_ma5 and not above_ma20:
            if ma5 < ma20:
                label  = "Bearish"
                detail = f"Price is below both MA5 ({ma5}) and MA20 ({ma20}), with MA5 below MA20."
                css    = "red"
            else:
                label  = "Trend Reversal (Bearish)"
                detail = f"Price broke below MA5 ({ma5}) while MA20 ({ma20}) is still below — early reversal signal."
                css    = "orange"
        else:
            label  = "Sideways"
            detail = f"Mixed signals — price near MA5 ({ma5}) and MA20 ({ma20})."
            css    = "gray"
    else:
        # Only MA5 available
        if above_ma5:
            label, detail, css = "Bullish", f"Price is above MA5 ({ma5}).", "green"
        else:
            label, detail, css = "Bearish", f"Price is below MA5 ({ma5}).", "red"

    return TrendSignal(label=label, ma5=ma5, ma20=ma20, css_class=css, detail=detail)


def _classify_breakout(
    close: float,
    prev_rows: list[StockDailyData],
) -> BreakoutSignal:
    """Check if price broke above 20-day high or below 20-day low."""
    if not prev_rows:
        return BreakoutSignal(False, False, None, None, "Insufficient Data", "gray")

    highs = [r.high_price for r in prev_rows[:20]]
    lows  = [r.low_price  for r in prev_rows[:20]]

    prev_high = max(highs) if highs else None
    prev_low  = min(lows)  if lows  else None

    breakout  = prev_high is not None and close > prev_high
    breakdown = prev_low  is not None and close < prev_low

    if breakout:
        label, css = "Resistance Breakout", "green"
    elif breakdown:
        label, css = "Support Breakdown",   "red"
    else:
        label, css = "Within Range",        "gray"

    return BreakoutSignal(
        breakout=breakout, breakdown=breakdown,
        prev_20d_high=prev_high, prev_20d_low=prev_low,
        label=label, css_class=css,
    )


def _classify_momentum(row: StockDailyData) -> MomentumSignal:
    """Intraday momentum: range % and close vs open %."""
    intraday_range_pct = 0.0
    close_vs_open_pct  = 0.0

    if row.open_price > 0:
        intraday_range_pct = round(_safe_div(row.high_price - row.low_price, row.open_price) * 100, 2)
        close_vs_open_pct  = round(_safe_div(row.close_price - row.open_price, row.open_price) * 100, 2)

    if close_vs_open_pct >= 3:
        label, css = "Strong Positive", "green"
    elif close_vs_open_pct >= 0.5:
        label, css = "Moderate Positive", "lime"
    elif close_vs_open_pct >= -0.5:
        label, css = "Weak / Flat", "gray"
    elif close_vs_open_pct >= -3:
        label, css = "Moderate Negative", "orange"
    else:
        label, css = "Strong Negative", "red"

    return MomentumSignal(
        label=label,
        intraday_range_pct=intraday_range_pct,
        close_vs_open_pct=close_vs_open_pct,
        css_class=css,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Explanation generator
# ─────────────────────────────────────────────────────────────────────────────

def _generate_explanation(
    price_class: PriceClassification,
    volume:      VolumeSignal,
    trend:       TrendSignal,
    breakout:    BreakoutSignal,
    momentum:    MomentumSignal,
    change_pct:  float,
) -> tuple[str, list[str], int]:
    """
    Returns (primary_reason, supporting_reasons, confidence_score).
    """
    reasons    = []
    confidence = 40   # base

    is_up   = change_pct > 0
    is_down = change_pct < 0

    # ── primary reason ──
    if breakout.breakout:
        primary = (
            f"Stock surged after breaking above its 20-day resistance level "
            f"(NPR {breakout.prev_20d_high:,.2f}), signalling strong buyer conviction."
        )
        confidence += 20
    elif breakout.breakdown:
        primary = (
            f"Stock fell after breaking below its 20-day support level "
            f"(NPR {breakout.prev_20d_low:,.2f}), indicating selling pressure overwhelmed buyers."
        )
        confidence += 20
    elif is_up and "Bullish" in trend.label:
        primary = (
            "Stock continued its established uptrend, with buyers maintaining control "
            "across both short-term and medium-term timeframes."
        )
        confidence += 15
    elif is_down and "Bearish" in trend.label:
        primary = (
            "Stock declined in line with its prevailing downtrend, "
            "with sellers dominating price action throughout the session."
        )
        confidence += 15
    elif "Reversal" in trend.label:
        direction = "upward" if is_up else "downward"
        primary = (
            f"Price showed a potential {direction} trend reversal, "
            "diverging from recent momentum — watch closely for confirmation."
        )
        confidence += 10
    elif abs(change_pct) < 1:
        primary = (
            "Price movement was minimal, reflecting a balanced session with "
            "neither buyers nor sellers gaining significant ground."
        )
    elif is_up:
        primary = (
            f"Stock gained {abs(change_pct):.2f}% without a clear structural catalyst — "
            "likely driven by general market sentiment or sector rotation."
        )
    else:
        primary = (
            f"Stock declined {abs(change_pct):.2f}% without a clear structural trigger — "
            "likely driven by profit-booking or general market weakness."
        )

    # ── supporting reasons ──
    if volume.label in ("High", "Extreme"):
        vol_text = (
            f"Trading volume was {volume.ratio:.1f}× the 20-day average "
            f"({int(volume.avg_20d):,} shares), confirming strong participant interest."
        )
        reasons.append(vol_text)
        confidence += 15
    elif volume.label == "Elevated":
        reasons.append(
            f"Volume was moderately elevated at {volume.ratio:.1f}× the 20-day average, "
            "suggesting above-normal activity without a full demand surge."
        )
        confidence += 8
    else:
        reasons.append(
            "Volume was within normal range, suggesting this move may lack broad market conviction."
        )

    if momentum.close_vs_open_pct >= 2:
        reasons.append(
            f"Intraday momentum was strongly positive — stock closed {momentum.close_vs_open_pct:.1f}% "
            "above its open, showing buyers were active throughout the session."
        )
        confidence += 10
    elif momentum.close_vs_open_pct <= -2:
        reasons.append(
            f"Intraday selling pressure was heavy — stock closed {abs(momentum.close_vs_open_pct):.1f}% "
            "below its open, indicating sellers dominated the full session."
        )
        confidence += 10

    if trend.ma5 and trend.ma20:
        reasons.append(f"Trend context: MA5 = NPR {trend.ma5:,.2f}, MA20 = NPR {trend.ma20:,.2f}. {trend.detail}")
    elif trend.ma5:
        reasons.append(f"Short-term MA5 = NPR {trend.ma5:,.2f}. {trend.detail}")

    if momentum.intraday_range_pct > 5:
        reasons.append(
            f"Wide intraday range of {momentum.intraday_range_pct:.1f}% indicates high volatility "
            "and uncertainty during the session."
        )

    # cap confidence
    confidence = min(confidence, 95)

    return primary, reasons, confidence


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def explain_stock_movement(symbol: str, target_date: date) -> AnalysisResult:
    """
    Main entry point. Returns a fully populated AnalysisResult.
    On any error, returns an AnalysisResult with .error set.
    """
    symbol = symbol.upper().strip()

    # ── fetch target row ──────────────────────────────────────────────────
    try:
        row = StockDailyData.objects.get(symbol=symbol, date=target_date)
    except StockDailyData.DoesNotExist:
        return AnalysisResult(
            symbol=symbol,
            target_date=target_date,
            row=None,
            price_class=PriceClassification("N/A", "gray", "❓"),
            volume=VolumeSignal("N/A", 0, 0, "gray"),
            trend=TrendSignal("N/A", None, None, "gray", ""),
            breakout=BreakoutSignal(False, False, None, None, "N/A", "gray"),
            momentum=MomentumSignal("N/A", 0, 0, "gray"),
            primary_reason="",
            supporting_reasons=[],
            confidence_score=0,
            error=f"No data found for {symbol} on {target_date}. "
                  "Please check the symbol or select a trading day.",
        )

    # ── fetch previous rows (newest-first, up to 20 before target) ────────
    prev_rows = list(
        StockDailyData.objects
        .filter(symbol=symbol, date__lt=target_date)
        .order_by("-date")[:20]
    )

    # ── recent history for table (10 rows before target) ─────────────────
    recent_history = list(
        StockDailyData.objects
        .filter(symbol=symbol, date__lte=target_date)
        .order_by("-date")[:11]         # includes target row itself
    )

    # ── run signals ───────────────────────────────────────────────────────
    price_class = _classify_price(row.change_percent)
    volume      = _classify_volume(row.volume, prev_rows)
    trend       = _classify_trend(row.close_price, prev_rows)
    breakout    = _classify_breakout(row.close_price, prev_rows)
    momentum    = _classify_momentum(row)

    # ── generate explanation ──────────────────────────────────────────────
    primary, supporting, confidence = _generate_explanation(
        price_class, volume, trend, breakout, momentum, row.change_percent
    )

    return AnalysisResult(
        symbol=symbol,
        target_date=target_date,
        row=row,
        price_class=price_class,
        volume=volume,
        trend=trend,
        breakout=breakout,
        momentum=momentum,
        primary_reason=primary,
        supporting_reasons=supporting,
        confidence_score=confidence,
        recent_history=recent_history,
        error=None,
    )

def get_all_symbols() -> list[str]:
    """Return sorted list of all distinct stock symbols in the database."""
    return list(
        StockDailyData.objects
        .values_list("symbol", flat=True)
        .distinct()
        .order_by("symbol")
    )