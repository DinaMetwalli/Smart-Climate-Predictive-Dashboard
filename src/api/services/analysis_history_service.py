from src.utils.database_config import db
import datetime;

class AnalysisHistoryService():
    def __init__(self):
        print("Initialising History Saving Service...")

    def save_custom_analysis_results(self, user_id: str, analysis_name: str, filenames: list) -> bool:
        
        self.create_analysis_entry(user_id, analysis_name)
        
        analysis_id = db.execute_and_fetch_one(
            "SELECT id FROM analysis_history WHERE analysis_name = %s AND user_id = %s",
            analysis_name, user_id
        )
        
        print(f"Analysis {analysis_name} saved to database with ID {analysis_id}.")

        self.save_file_info(filenames, analysis_id)

        return True
    
    def create_analysis_entry(self, user_id:str, analysis_name: str) -> None:
        timestamp = datetime.datetime.now()
        db.execute_and_commit(
            "INSERT INTO analysis_history (analysis_name, creation_timestamp, user_id) VALUES (%s, %s, %s)",
            analysis_name, timestamp, user_id
            )
        
    def save_file_info(self, filenames:list, analysis_id: str) -> None:
        for file in filenames:
            db.execute_and_commit(
                "INSERT INTO analysis_uploads (dataset_file_name, analysis_id) VALUES (%s, %s)",
                file, analysis_id 
            )

    def save_prediction_values(self, analysis_id) -> None:
        pass

    def get_user_analyses(self, user_id) -> list:
        analyses = db.execute_and_fetch_all("SELECT * FROM analysis_history WHERE user_id = %s",
                                            user_id)
        
        print(analyses)
        return analyses