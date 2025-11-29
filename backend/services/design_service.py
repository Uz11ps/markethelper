import re
from typing import Iterable, Sequence

from backend.models import DesignTemplate


def _tokenize(text: str) -> set[str]:
    cleaned = (text or "").lower()
    if not cleaned:
        return set()
    tokens = re.split(r"[^a-zа-яё0-9]+", cleaned)
    return {token for token in tokens if token}


async def create_template(**data) -> DesignTemplate:
    """
    Создаёт новый пресет инфографики.
    """
    return await DesignTemplate.create(**data)


def _score_template(template: DesignTemplate, tokens: set[str]) -> tuple[int, int]:
    """
    Возвращает кортеж для сортировки: (score, tag_matches).
    """
    if not tokens:
        return 0, 0
    haystacks: Iterable[str] = [
        template.name or "",
        template.prompt or "",
        template.theme_tags or "",
    ]
    score = 0
    tag_matches = 0
    for token in tokens:
        matched = False
        for hay in haystacks:
            if token in (hay or "").lower():
                score += 1
                matched = True
        if matched and token in _tokenize(template.theme_tags or ""):
            tag_matches += 1
    return score, tag_matches


async def search_templates(
    template_type: str,
    query: str | None,
    limit: int = 3,
) -> Sequence[DesignTemplate]:
    """
    Возвращает подходящие шаблоны инфографики.
    """
    templates = await DesignTemplate.filter(type=template_type).all()
    if not templates:
        return []

    if not query:
        return templates[:limit]

    tokens = _tokenize(query)
    if not tokens:
        return templates[:limit]

    scored = []
    for template in templates:
        score, tag_score = _score_template(template, tokens)
        scored.append((score, tag_score, template))

    # Сортируем: сначала по количеству совпадений, затем по тегам и id (чтобы порядок был стабильным)
    scored.sort(key=lambda item: (item[0], item[1], item[2].id), reverse=True)

    return [item[2] for item in scored[:limit] if item[0] > 0] or templates[:limit]
