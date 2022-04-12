class Character:
    def __init__(self, name):
        self.name = name
        self.stats = {}

    def __str__(self):
        return self.name

    def set_stats(self, d):
        self.stats.update(d)

    def get_stats(self):
        s = "\n".join([f"{k}:{v}" for k, v in self.stats.items()])
        return f"**Stats:**\n{s}"
