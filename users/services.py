def normalize_phone(phone: str) -> str:
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if phone.startswith("8") and len(phone) == 11:
        return "+7" + phone[1:]
    return phone
