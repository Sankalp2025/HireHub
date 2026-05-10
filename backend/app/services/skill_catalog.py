import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class SkillPhrase:
    phrase: str
    category: str
    aliases: tuple[str, ...]


@lru_cache
def load_skill_phrases() -> tuple[SkillPhrase, ...]:
    path = Path(__file__).resolve().parents[1] / "data" / "skill_phrases.json"

    with path.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    return tuple(
        SkillPhrase(
            phrase=item["phrase"],
            category=item["category"],
            aliases=tuple(item.get("aliases", [])),
        )
        for item in raw_items
    )
