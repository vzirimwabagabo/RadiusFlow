def apply_pagination(query, page: int = 1, page_size: int = 50):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 500)
    return query.offset((page - 1) * page_size).limit(page_size)
