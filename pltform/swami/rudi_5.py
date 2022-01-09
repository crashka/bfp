# -*- coding: utf-8 -*-

from ..team import Team
from ..game import GameInfo
from .base import Swami

class SwamiRudi5(Swami):
    """Rudimentary prediction based on last two matchups between teams
    """
    name = "Rudi 5"
    desc = "Based on last two matchups between teams"

    def __init__(self, opp: Team):
        pass

    def pick_winner(self, game_info: GameInfo) -> tuple[Team, int]:
        """Implement algorithm to pick winner of games

        :param game_info: context/schedule info for the game
        :return: predicted winning team and margin of victory
        """
        pass