import json
import os

PROFILE_FILE = "user_profile.json"

class ProfileManager:
    def __init__(self, filepath=PROFILE_FILE):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            self.save_profile({})

    def load_profile(self) -> dict:
        with open(self.filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_profile(self, profile: dict):
        with open(self.filepath, 'w') as f:
            json.dump(profile, f, indent=4)

    def update_profile(self, new_data: dict):
        profile = self.load_profile()
        profile.update(new_data)
        self.save_profile(profile)

    def get_profile_string(self) -> str:
        return json.dumps(self.load_profile(), indent=2)
