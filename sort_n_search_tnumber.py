def sort_contacts(contacts, column, reverse=False):
    """
    Сортирует список контактов по указанному полю.
    column — 'name' | 'phone' | 'comment'
    """
    return sorted(contacts,
                  key=lambda c: c.get(column, "").lower(),
                  reverse=reverse)


def search_contacts(contacts, query):
    """
    Возвращает список контактов, у которых query встречается
    в имени, телефоне или комментарии (без учёта регистра).
    """
    if not query:
        return contacts[:]
    q = query.lower()
    return [
        c for c in contacts
        if q in c.get("name", "").lower()
        or q in c.get("phone", "").lower()
        or q in c.get("comment", "").lower()
    ]