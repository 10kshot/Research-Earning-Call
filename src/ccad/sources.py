"""Where transcripts come from. Every source yields (file_name, raw XML) pairs,
so the parser and everything downstream are the same whichever source is used.

- LocalXMLSource: data/raw/transcripts/<year>/*_T.xml (2016 today).
- SupabaseSource: the lab database, still locked as of 2026-10-04. Its schema
  is unconfirmed; the old risk/activeness code only ever read scores
  (`documents`) and matched sentences (`keyword_matches`) from it, never full
  transcript text. Fill in `TABLE` / columns once access is restored.
"""

import os
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class LocalXMLSource:
    def __init__(self, base: Path = ROOT / "data" / "raw" / "transcripts"):
        self.base = Path(base)

    def years(self) -> list[int]:
        return sorted(int(p.name) for p in self.base.iterdir() if p.is_dir() and p.name.isdigit())

    def iter_xml(self, year: int) -> Iterator[tuple[str, bytes]]:
        for f in sorted((self.base / str(year)).glob("*_T.xml")):
            yield f.name, f.read_bytes()


class SupabaseSource:
    """Reads SUPABASE_URL and SUPABASE_ANON_KEY from the environment (or a git-ignored .env)."""

    TABLE = None  # TODO: table holding full transcript XML/text, once confirmed
    XML_COLUMN = None
    NAME_COLUMN = None
    YEAR_COLUMN = "year"
    PAGE = 1000

    def __init__(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            pass
        from supabase import create_client  # pip install supabase
        self.client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

    def iter_xml(self, year: int) -> Iterator[tuple[str, bytes]]:
        if not (self.TABLE and self.XML_COLUMN and self.NAME_COLUMN):
            raise NotImplementedError("Supabase transcript table not configured yet; see module docstring.")
        offset = 0
        while True:
            rows = (self.client.table(self.TABLE)
                    .select(f"{self.NAME_COLUMN},{self.XML_COLUMN}")
                    .eq(self.YEAR_COLUMN, year)
                    .range(offset, offset + self.PAGE - 1)
                    .execute().data)
            if not rows:
                return
            for r in rows:
                yield r[self.NAME_COLUMN], r[self.XML_COLUMN].encode()
            offset += self.PAGE


def get_source(name: str):
    return {"local": LocalXMLSource, "supabase": SupabaseSource}[name]()
