"""Fiscal-to-calendar conversion using Compustat fiscal year-end month (FYR).

Quarters are represented as integer indices: year * 4 + (quarter - 1).
"""


def qidx(year: int, quarter: int) -> int:
    return year * 4 + (quarter - 1)


def qlabel(idx: int) -> str:
    return f"{idx // 4}Q{idx % 4 + 1}"


def fiscal_quarter_end(fyear: int, fqtr: int, fyr: int) -> tuple[int, int]:
    """(calendar year, month) in which fiscal quarter `fqtr` of `fyear` ends.

    Compustat convention: fiscal year `fyear` ends in calendar year `fyear` when
    FYR >= 6, otherwise in `fyear + 1`.
    """
    end_year = fyear if fyr >= 6 else fyear + 1
    months_before_fye = 3 * (4 - fqtr)
    m = fyr - months_before_fye
    y = end_year
    while m <= 0:
        m += 12
        y -= 1
    return y, m


def fiscal_to_calendar_qidx(fyear: int, fqtr: int, fyr: int) -> int:
    """Calendar quarter containing the end of the fiscal quarter."""
    y, m = fiscal_quarter_end(fyear, fqtr, fyr)
    return qidx(y, (m - 1) // 3 + 1)


def calendar_qidx_of_date(iso_date: str) -> int:
    y, m = int(iso_date[:4]), int(iso_date[5:7])
    return qidx(y, (m - 1) // 3 + 1)
