from dataclasses import dataclass

@dataclass
class UserStat:
    user_id: int
    username: str | None
    first_name: str
    total_actions: int

    @property
    def link(self) -> str:
        if self.username:
            return f"<a href=\"https://t.me/{self.username}\">@{self.username}</a>"

        return f"<a href=\"tg://user?id={self.user_id}\">{self.first_name}</a>"
