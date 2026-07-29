"""이터널리턴(Eternal Return) Open API 클라이언트.

공식 문서: https://developer.eternalreturn.io
token.env 의 ER_API_KEY 값을 사용합니다.
"""
import os

import aiohttp

ER_API_BASE = "https://open-api.bser.io/v1"


class ERAPIError(Exception):
    """이터널리턴 API 호출 실패 시 발생하는 예외."""


class EternalReturnAPI:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._character_names: dict[int, str] | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"x-api-key": os.getenv("ER_API_KEY")},
                timeout=aiohttp.ClientTimeout(total=15),
            )
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _get(self, path: str, params: dict | None = None) -> dict:
        session = await self._get_session()
        url = f"{ER_API_BASE}/{path.lstrip('/')}"
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise ERAPIError(f"HTTP {resp.status} on {url}: {text}")
            data = await resp.json()
            if data.get("code") != 200:
                raise ERAPIError(f"{data.get('code')}: {data.get('message')}")
            return data

    async def get_user_num(self, nickname: str) -> int:
        data = await self._get("user/nickname", params={"query": nickname})
        user = data.get("user")
        if not user:
            raise ERAPIError(f"'{nickname}' 닉네임을 찾을 수 없습니다.")
        return user["userNum"]

    async def get_user_games(self, user_num: int) -> list[dict]:
        """최근 90일간 유저의 전적(BattleUserResult 배열)을 가져옵니다."""
        data = await self._get(f"user/games/{user_num}")
        return data.get("userGames", []) or []

    async def get_character_names(self) -> dict[int, str]:
        """characterNum -> 캐릭터 이름 매핑. 실패 시 빈 dict를 반환합니다."""
        if self._character_names is not None:
            return self._character_names

        names: dict[int, str] = {}
        try:
            data = await self._get("data/Character")
            rows = data.get("data", []) or []
            for row in rows:
                code = row.get("code", row.get("Code"))
                name = row.get("name", row.get("Name"))
                if code is not None and name:
                    names[int(code)] = str(name)
        except Exception:
            # 데이터 테이블 형식이 문서화되어 있지 않아 실패할 수 있음.
            # 실패해도 캐릭터 코드 숫자로 대체 표시하므로 기능은 계속 동작함.
            names = {}

        self._character_names = names
        return names


er_api = EternalReturnAPI()
