from __future__ import annotations


class BaseEntity:
    """Shared base for Player and Enemy.

    Holds HP and Stamina pools with simple mutation helpers.
    Does not contain any combat or system logic — that lives in src/systems/.
    """

    def __init__(self, name: str, hp: int, stamina: int):
        self.name         = name
        self.max_hp       = hp
        self.hp           = hp
        self.max_stamina  = stamina
        self.stamina      = stamina

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def is_alive(self) -> bool:
        """Return True while HP is above zero."""
        pass

    @property
    def is_exhausted(self) -> bool:
        """Return True when stamina has reached zero (forces Defend action)."""
        pass

    # ── HP ───────────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> int:
        """Reduce HP by amount (clamped to 0). Return actual damage taken."""
        pass

    def heal(self, amount: int) -> int:
        """Restore HP by amount (clamped to max_hp). Return HP actually restored."""
        pass

    # ── Stamina ──────────────────────────────────────────────────────────────

    def use_stamina(self, amount: int) -> bool:
        """Deduct stamina. Return False (and do nothing) if insufficient."""
        pass

    def restore_stamina(self, amount: int) -> None:
        """Add stamina up to max_stamina."""
        pass

    def recover_between_rounds(self) -> None:
        """Partially restore stamina at the end of each combat round."""
        pass

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise core state to a JSON-compatible dict."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name!r} HP={self.hp}/{self.max_hp}>"
