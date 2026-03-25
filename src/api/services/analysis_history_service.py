from src.utils.database_config import db
from collections import defaultdict
import datetime;

class AnalysisHistoryService():
    def __init__(self):
        print("Initialising History Saving Service...")

    def save_custom_analysis_results(self, user_id: str, analysis_name: str, filenames: list, predictions:dict) -> bool:
        
        self.create_analysis_entry(user_id, analysis_name)
        
        analysis_id = db.execute_and_fetch_one(
            "SELECT id FROM analysis_history WHERE analysis_name = %s AND user_id = %s",
            analysis_name, user_id
        )
        
        print(f"Analysis {analysis_name} saved to database with ID {analysis_id}.")

        self.save_file_info(filenames, analysis_id)
        self.save_prediction_values(analysis_id, predictions)

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

    def save_prediction_values(self, analysis_id, predictions) -> None:
        for region, values in predictions.items():
            region_id = db.execute_and_fetch_one(
                "SELECT id FROM regions WHERE region = %s",
                region
            )
            for i in range(1, len(values)+1):
                db.execute_and_commit(
                    "INSERT INTO predictions (month_index, prediction_val, analysis_id, region_id) VALUES (%s, %s, %s, %s)",
                    i, round(values[i-1], 3), analysis_id, region_id
                )

    def get_user_analyses(self, user_id) -> list:
        analyses = db.execute_and_fetch_all("SELECT * FROM analysis_history WHERE user_id = %s",
                                            user_id)
        
        return analyses
    
    def get_prediction_values(self, analysis_id):
        predictions = defaultdict(list)
        preds_result = db.execute_and_fetch_all(
                "SELECT r.region, p.id, p.month_index, p.prediction_val, p.analysis_id, p.region_id \
                FROM predictions p \
                INNER JOIN regions r \
                ON r.id = p.region_id \
                WHERE p.analysis_id = %s",
                analysis_id
            )
        
        for pred in preds_result:
            predictions[pred[0]].append(float(pred[3]))
        
        return predictions
    
    def delete_analysis(self, analysis_ids:list) -> None:
        analyses_tuple = tuple(analysis_ids)

        db.execute_and_commit("DELETE FROM predictions WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_uploads WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_history WHERE id IN %s", analyses_tuple)

    def delete_all_analyses(self, user_id) -> None:
        analyses = db.execute_and_fetch_all("SELECT id FROM analysis_history WHERE user_id = %s", user_id)
        analyses_tuple = tuple(analysis[0] for analysis in analyses)

        db.execute_and_commit("DELETE FROM predictions WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_uploads WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_history WHERE id IN %s", analyses_tuple)