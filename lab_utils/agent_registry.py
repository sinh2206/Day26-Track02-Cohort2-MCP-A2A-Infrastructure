"""Agent registry in-memory với capability discovery và Agent Card health check."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx


@dataclass
class RegisteredAgent:
    name: str
    url: str
    description: str
    capabilities: dict[str, Any] = field(default_factory=dict)
    healthy: bool = True
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {}

    def register(self, agent: RegisteredAgent) -> None:
        self._agents[agent.name] = agent

    def deregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def set_health(self, name: str, healthy: bool) -> None:
        if name in self._agents:
            self._agents[name].healthy = healthy

    def list_agents(self, healthy_only: bool = False) -> list[RegisteredAgent]:
        agents = list(self._agents.values())
        if healthy_only:
            agents = [agent for agent in agents if agent.healthy]
        return agents

    def find_by_capability(self, keyword: str) -> list[RegisteredAgent]:
        keyword_lower = keyword.casefold()
        return [
            agent
            for agent in self._agents.values()
            if keyword_lower in agent.description.casefold()
            or keyword_lower in str(agent.capabilities).casefold()
        ]

    def check_health(self, name: str, timeout: float = 3.0) -> bool:
        """Kiểm tra Agent Card và cập nhật trạng thái của một agent."""
        agent = self._agents.get(name)
        if agent is None:
            return False
        card_url = (
            agent.url
            if agent.url.endswith("/.well-known/agent-card.json")
            else f"{agent.url.rstrip('/')}/.well-known/agent-card.json"
        )
        try:
            response = httpx.get(card_url, timeout=timeout)
            response.raise_for_status()
            response.json()
            agent.healthy = True
        except (httpx.HTTPError, ValueError):
            agent.healthy = False
        return agent.healthy

    def refresh_health(self, timeout: float = 3.0) -> dict[str, bool]:
        """Kiểm tra tất cả agent đã đăng ký."""
        return {name: self.check_health(name, timeout) for name in self._agents}
