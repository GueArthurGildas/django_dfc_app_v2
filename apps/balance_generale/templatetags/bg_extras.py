from django import template

register = template.Library()


@register.filter
def en_millions(valeur):
    """Convertit un montant FCFA en Millions avec 1 décimale. Ex: 13734486673 → 13 734,5 M"""
    if valeur is None:
        return "—"
    try:
        v = float(valeur)
        m = v / 1_000_000
        if m == 0:
            return "0"
        if abs(m) >= 1000:
            return f"{m:,.0f} M"
        return f"{m:,.1f} M"
    except (TypeError, ValueError):
        return "—"


@register.filter
def en_milliards(valeur):
    """Convertit un montant FCFA en Milliards. Ex: 418456500639 → 418,5 Mrd"""
    if valeur is None:
        return "—"
    try:
        v   = float(valeur)
        mrd = v / 1_000_000_000
        return f"{mrd:,.1f} Mrd"
    except (TypeError, ValueError):
        return "—"


@register.filter
def fmt_fcfa(valeur):
    """Format intelligent : Mrd si > 1 Mrd, M sinon."""
    if valeur is None:
        return "—"
    try:
        v = float(valeur)
        if v == 0:
            return "0"
        if abs(v) >= 1_000_000_000:
            return f"{v/1_000_000_000:,.1f} Mrd"
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:,.1f} M"
        return f"{v:,.0f}"
    except (TypeError, ValueError):
        return "—"


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
