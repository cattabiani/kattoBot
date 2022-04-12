from src import character


class GameException(Exception):
    pass


class Game:
    def __init__(self):
        self.dm = None
        self.characters = {}

    def get_characters(self):
        s = "\n".join([f"{k}:{v}" for k, v in self.characters.items()])
        return s

    def create_character(self, player, char_name):
        if player in self.characters:
            raise GameException(
                f"Player `{player}` has already the character `{self.characters[player]}`"
            )

        self.characters[player] = character.Character(char_name)
