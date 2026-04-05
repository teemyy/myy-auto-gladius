from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.team import Team


@dataclass
class Match:
    """A single scheduled bout between two teams."""
    home: "Team"
    away: "Team"
    played: bool = False


@dataclass
class MatchResult:
    """The recorded outcome of a played match."""
    match:      Match
    winner:     "Team"
    loser:      "Team"
    home_gold:  int = 0
    away_gold:  int = 0


@dataclass
class StandingsEntry:
    """One row in the tournament standings table."""
    team:        "Team"
    wins:        int = 0
    losses:      int = 0
    gold_earned: int = 0

    def win_rate(self) -> float:
        """Return wins / total fights; 0.0 if no fights played."""
        pass


class Tournament:
    """Manages a single round-robin tournament across all league teams.

    Responsibilities:
    - Generate the full round-robin schedule (every team vs every other team).
    - Accept match results and update standings.
    - Determine the winner (highest win rate; gold tiebreaker).
    - Award the trophy and prize gold to teams.
    """

    PRIZE_GOLD_WIN:  int = 150
    PRIZE_GOLD_LOSS: int = 50

    def __init__(self, teams: list["Team"]):
        self.teams:    list["Team"]        = teams
        self.schedule: list[Match]         = []
        self.results:  list[MatchResult]   = []
        self.standings: list[StandingsEntry] = []
        self.is_complete: bool             = False

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def generate_schedule(self) -> list[Match]:
        """Build the round-robin fixture list and store it on self.schedule.

        Every (home, away) pair appears exactly once.  Returns the schedule.
        """
        pass

    def build_standings(self) -> list[StandingsEntry]:
        """Initialise a StandingsEntry for every team and store on self.standings."""
        pass

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def next_match(self) -> Match | None:
        """Return the next unplayed match, or None if all matches are done."""
        pass

    def record_result(self, result: MatchResult) -> None:
        """Store a result and update standings for both teams.

        Also distributes prize gold via ``PRIZE_GOLD_WIN`` / ``PRIZE_GOLD_LOSS``.
        """
        pass

    def remaining_matches(self) -> list[Match]:
        """Return all matches not yet played."""
        pass

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def sorted_standings(self) -> list[StandingsEntry]:
        """Return standings sorted by win rate desc, gold earned desc (tiebreaker)."""
        pass

    def get_winner(self) -> "Team | None":
        """Return the tournament winner, or None if the tournament is unfinished."""
        pass

    def award_trophy(self) -> None:
        """Increment the winner's trophy count and mark the tournament complete."""
        pass

    def is_finished(self) -> bool:
        """Return True when all scheduled matches have been played."""
        pass

    def __repr__(self) -> str:
        played = sum(1 for m in self.schedule if m.played)
        total  = len(self.schedule)
        return f"<Tournament {played}/{total} matches played>"
