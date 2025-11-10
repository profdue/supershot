import pandas as pd
import os

class DataLoader:
    def __init__(self, data_path="data"):
        self.data_path = data_path
        
    def load_teams_data(self):
        """Load team performance data"""
        try:
            file_path = os.path.join(self.data_path, "teams.csv")
            df = pd.read_csv(file_path)
            print(f"✅ Loaded teams data: {len(df)} records")
            return df
        except FileNotFoundError:
            print(f"❌ Teams data file not found at {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading teams data: {e}")
            return None
            
    def load_team_quality_data(self):
        """Load team quality data (Elo, squad value)"""
        try:
            file_path = os.path.join(self.data_path, "team_quality.csv")
            df = pd.read_csv(file_path)
            print(f"✅ Loaded team quality data: {len(df)} records")
            return df
        except FileNotFoundError:
            print(f"❌ Team quality data file not found at {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading team quality data: {e}")
            return None
            
    def load_home_advantage_data(self):
        """Load home advantage data"""
        try:
            file_path = os.path.join(self.data_path, "home_advantage.csv")
            df = pd.read_csv(file_path)
            print(f"✅ Loaded home advantage data: {len(df)} records")
            return df
        except FileNotFoundError:
            print(f"❌ Home advantage data file not found at {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading home advantage data: {e}")
            return None
            
    def load_all_data(self):
        """Load all datasets and return as dictionary"""
        data = {
            'teams': self.load_teams_data(),
            'team_quality': self.load_team_quality_data(),
            'home_advantage': self.load_home_advantage_data()
        }
        
        # Check if all data loaded successfully
        success = all(value is not None for value in data.values())
        if success:
            print("🎯 All data loaded successfully!")
        else:
            print("⚠️ Some data failed to load")
            
        return data
