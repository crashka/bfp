# -*- coding: utf-8 -*-

from ..game import GameInfo, Pick
from ..analysis import AnlyFilterDiv
from .cyber_basic import SwamiCyberBasic

class SwamiVsDiv(SwamiCyberBasic):
    """Rudimentary prediction based on most recent games against a specific
    opponent team
    """
    def make_pick(self, game_info: GameInfo) -> Pick | None:
        """Implement algorithm to pick winner of games

        :param game_info: context/schedule info for the game
        :return: predictions and confidence for both SU and ATS
        """
        home_team = game_info.home_team
        away_team = game_info.away_team
        opp_filter = {home_team: AnlyFilterDiv(away_team.div),
                      away_team: AnlyFilterDiv(home_team.div)}

        return self.cyber_pick(game_info, [opp_filter])
