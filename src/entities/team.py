from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gladiator import Gladiator


class TeamRecord:
    """Win/loss/gold record for a single tournament."""

    def __init__(self):
        self.wins:       int = 0
        self.losses:     int = 0
        self.gold_earned: int = 0

    def win_rate(self) -> float:
        """Return wins / total fights, or 0.0 if no fights played."""
        pass


class Team:
    """A team in the league — either the player's team or an AI team.

    Holds the roster, gold balance, historical records, and trophy count.
    The ``is_player`` flag distinguishes AI teams from the human-controlled one.
    """

    MAX_ROSTER_SIZE = 4

    def __init__(self, name: str, is_player: bool = False):
        self.name:      str            = name
        self.is_player: bool           = is_player
        self.roster:    list[Gladiator] = []
        self.gold:      int            = 0
        self.trophies:  int            = 0
        self.current_record: TeamRecord          = TeamRecord()
        self.history:        list[TeamRecord]    = []  # one entry per tournament

    # ------------------------------------------------------------------
    # Roster management
    # ------------------------------------------------------------------

    def add_gladiator(self, gladiator: "Gladiator") -> bool:
        """Add a gladiator to the roster. Returns False if roster is full."""
        pass

    def remove_gladiator(self, gladiator: "Gladiator") -> bool:
        """Remove a gladiator from the roster. Returns False if not found."""
        pass

    def available_gladiators(self) -> list["Gladiator"]:
        """Return gladiators who are healthy and able to fight."""
        pass

    def roster_size(self) -> int:
        """Return the current number of gladiators on the roster."""
        pass

    def is_full(self) -> bool:
        """Return True if the roster has reached MAX_ROSTER_SIZE."""
        pass

    # ------------------------------------------------------------------
    # Gold
    # ------------------------------------------------------------------

    def earn_gold(self, amount: int) -> None:
        """Add gold to the team balance and record it on the current record."""
        pass

    def spend_gold(self, amount: int) -> bool:
        """Deduct gold. Returns False and makes no change if funds insufficient."""
        pass

    # ------------------------------------------------------------------
    # Season / tournament lifecycle
    # ------------------------------------------------------------------

    def start_tournament(self) -> None:
        """Reset the current tournament record at the start of each tournament."""
        pass

    def end_tournament(self) -> None:
        """Archive the current record to history and award a trophy if won."""
        pass

    def advance_season(self) -> None:
        """Tick all gladiators' season counters; remove retired/dead gladiators."""
        pass

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict for save files."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        """Reconstruct a Team from a saved dict."""
        pass

    def __repr__(self) -> str:
        return (
            f"<Team {self.name!r} gold={self.gold} "
            f"roster={self.roster_size()}/{self.MAX_ROSTER_SIZE}>"
        )
