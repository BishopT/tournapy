import math
from enum import Enum

import pandas as pd


class Rank(Enum):
    @classmethod
    def from_label(cls, label: str):
        for e in cls:
            if e.value['label'] == label:
                return e

    @classmethod
    def from_elo(cls, elo: int):
        for e in cls:
            if elo == e.value['elo']:
                return e

    @classmethod
    def as_list(cls) -> list[dict[str, int, str]]:
        return [e.value for e in cls]

    @property
    def elo(self) -> int:
        return self.value['elo']

    @property
    def emoji(self) -> str:
        return self.value['emoji']


class Player:

    def __init__(self, name):
        self.__init__(name, 0)
        self.team: str = None  # team name

    def __init__(self, name, elo: int):
        self.name = name
        self.elo: int = elo
        self.team: str = None  # team name

    def set_team(self, team):
        self.team = team

    def as_series(self):
        return pd.Series(
            [self.name, self.elo, self.team],
            index=["name", "elo", "team"]
        )

    def __repr__(self):
        return f'{self.name} ({self.team})'


class Team:

    def __init__(self, name: str):
        self.name = name
        self.size = 0
        self.elo = 0
        self.points = 0
        self.goals_scored = 0
        self.goals_taken = 0

    def set_name(self, name: str):
        self.name = name

    def as_series(self):
        return pd.Series([self.name, self.elo, self.points, self.goals_scored - self.goals_taken],
                         index=["name", "elo", "points", "goals diff"])

    def __repr__(self):
        return f'{self.name} ({self.elo})'


class Match:

    def __init__(self, id: str, bo: int, blue_team: str, red_team: str):
        self.id = id
        self.bo = bo
        self.blue_team = blue_team
        self.red_team = red_team
        self.blue_score: list[int] = []
        self.red_score: list[int] = []
        self.bo_blue_score: int = 0
        self.bo_red_score: int = 0
        self.ended = False

    def __repr__(self):
        return f'{self.blue_team} : {self.bo_blue_score} - {self.bo_red_score} : {self.red_team}'

    def __json__(self, **options):
        return {self.blue_team: self.bo_blue_score, self.red_team: self.bo_red_score}

    def add_game_result(self, blue_score, red_score):
        if len(self.blue_score) < self.bo and not self.ended:
            self.blue_score.append(blue_score)
            self.red_score.append(red_score)
        else:
            raise Exception("BO is over, cannot add more games.")

    def set_result(self, game, blue_score, red_score):
        self.blue_score[game - 1] = blue_score
        self.red_score[game - 1] = red_score

    def get_result(self):
        return [self.blue_team, self.blue_score,
                self.red_team, self.red_score,
                self.get_winner()]

    def compute_bo(self) -> bool:
        self.bo_blue_score = 0
        self.bo_red_score = 0
        for i in range(len(self.blue_score)):
            self.bo_blue_score += 1 if (self.blue_score[i] >
                                        self.red_score[i]) else 0
            self.bo_red_score += 1 if (self.red_score[i]
                                       > self.blue_score[i]) else 0
        if self.bo_blue_score == math.ceil(self.bo / 2) or self.bo_red_score == math.ceil(self.bo / 2):
            self.ended = True
        return self.ended

    def get_winner(self) -> str:
        if self.bo_blue_score == self.bo_red_score:
            return None
        if self.bo_blue_score > self.bo_red_score:
            return self.blue_team
        else:
            return self.red_team
