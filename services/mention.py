from aiogram.utils.markdown import hlink

def get_user_link(
    *,
    user_id: int,
    username: str | None,
    first_name: str
) -> str:
    if username:
        url = f"https://t.me/{username}"

        return hlink(title=username, url=url)

    url = f"tg://user?id={user_id}"
    return hlink(title=first_name, url=url)