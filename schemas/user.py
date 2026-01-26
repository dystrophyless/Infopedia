from dataclasses import dataclass
from services.mention import get_user_link

@dataclass
class UserStat:
    user_id: int
    username: str | None
    first_name: str
    total_actions: int

    @property
    def link(self) -> str:
        return get_user_link(user_id=self.user_id, username=self.username, first_name=self.first_name)
