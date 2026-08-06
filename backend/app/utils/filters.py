def apply_exact_filter(query, model, field_name: str, value):
    if value is None:
        return query
    return query.filter(getattr(model, field_name) == value)
