from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.team import Team
    from ..entities.gladiator import Gladiator
    from ..entities.weapon import Weapon
    from ..entities.armor import Armor


class ShopListing:
    """A single item available for purchase in the between-tournament shop."""

    def __init__(self, item: "Weapon | Armor | Gladiator", price: int):
        self.item:      "Weapon | Armor | Gladiator" = item
        self.price:     int  = price
        self.sold:      bool = False


class EconomySystem:
    """Handles all gold transactions and shop inventory between tournaments.

    Responsibilities:
    - Calculate and distribute prize gold after each match result.
    - Generate a fresh shop inventory between tournaments.
    - Process player purchases and sales.
    - Apply the same buy/sell logic for AI teams.
    """

    STARTING_GOLD:      int = 500
    RECRUIT_BASE_PRICE: int = 200  # base cost before stat modifiers
    SELL_RATIO:        float = 0.5  # fraction of buy price recovered on sell

    # Prize gold constants live on Tournament; Economy reads them from there.

    def __init__(self):
        self.shop_inventory: list[ShopListing] = []

    # ------------------------------------------------------------------
    # Shop
    # ------------------------------------------------------------------

    def generate_shop(self, season: int) -> list[ShopListing]:
        """Populate shop_inventory with weapons, armors, and recruitable gladiators.

        Item quality and price scale with the current season number.
        Returns the new inventory list.
        """
        pass

    def buy_item(self, team: "Team", listing: ShopListing) -> bool:
        """Attempt to purchase a listing for a team.

        Deducts gold, marks the listing as sold, and adds the item to the team.
        Returns False if the team cannot afford it or the listing is already sold.
        """
        pass

    def sell_weapon(self, team: "Team", gladiator: "Gladiator") -> int:
        """Unequip and sell the gladiator's weapon. Returns gold received."""
        pass

    def sell_armor(self, team: "Team", gladiator: "Gladiator") -> int:
        """Unequip and sell the gladiator's armor. Returns gold received."""
        pass

    def recruit_gladiator(self, team: "Team", listing: ShopListing) -> bool:
        """Recruit the gladiator in the listing if the team has room and gold.

        Returns False if the roster is full or funds are insufficient.
        """
        pass

    # ------------------------------------------------------------------
    # Prizes
    # ------------------------------------------------------------------

    def distribute_match_prizes(
        self,
        winner: "Team",
        loser:  "Team",
        win_prize:  int,
        loss_prize: int,
    ) -> None:
        """Credit prize gold to both teams after a match."""
        pass

    def starting_gold(self, team: "Team") -> None:
        """Set a team's gold to STARTING_GOLD (called at new-game initialisation)."""
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def available_listings(self) -> list[ShopListing]:
        """Return only unsold shop listings."""
        pass

    def item_sell_price(self, item: "Weapon | Armor") -> int:
        """Return the sell price for a given item."""
        pass
