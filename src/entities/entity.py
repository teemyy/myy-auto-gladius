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
        return self.hp > 0

    @property
    def is_exhausted(self) -> bool:
        """Return True when stamina has reached zero (forces Defend action)."""
        return self.stamina <= 0

    # ── HP ───────────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> int:
        """Reduce HP by amount (clamped to 0). Return actual damage taken."""
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        """Restore HP by amount (clamped to max_hp). Return HP actually restored."""
        space = self.max_hp - self.hp
        actual = min(amount, space)
        self.hp += actual
        return actual

    # ── Stamina ──────────────────────────────────────────────────────────────

    def use_stamina(self, amount: int) -> bool:
        """Deduct stamina. Return False (and do nothing) if insufficient."""
        if self.stamina < amount:
            return False
        self.stamina -= amount
        return True

    def restore_stamina(self, amount: int) -> None:
        """Add stamina up to max_stamina."""
        self.stamina = min(self.stamina + amount, self.max_stamina)

    def recover_between_rounds(self) -> None:
        """Partially restore stamina at the end of each combat round."""
        pass

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise core state to a JSON-compatible dict."""
        return {
            "name":        self.name,
            "hp":          self.hp,
            "max_hp":      self.max_hp,
            "stamina":     self.stamina,
            "max_stamina": self.max_stamina,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name!r} HP={self.hp}/{self.max_hp}>"
