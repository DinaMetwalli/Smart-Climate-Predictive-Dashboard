from src.utils.database_config import db
from collections import defaultdict
from datetime import datetime

class AnalysisHistoryService():
    def __init__(self):
        print("Initialising History Saving Service...")

    def save_custom_analysis_results(self, user_id: str,
                                     analysis_name: str,
                                     filenames: list,
                                     predictions:dict,
                                     stats: dict,
                                     errors: dict,
                                     start_date: datetime) -> bool:
        
        analysis_id = self.create_analysis_entry(user_id, analysis_name, start_date)

        # Fetch region IDs map once to be reused in saving predictions, errors, and stats
        regions = list(predictions.keys())
        region_id_map = {
            region: db.execute_and_fetch_one("SELECT id FROM regions WHERE region = %s", region)
            for region in regions
        }
        
        print(f"Analysis {analysis_name} saved to database with ID {analysis_id}.")

        self.save_file_info(filenames, analysis_id)
        self.save_prediction_values(analysis_id, predictions, region_id_map)
        self.save_analysis_stats(analysis_id, stats, region_id_map)
        self.save_analysis_errors(analysis_id, errors, region_id_map)

        return True
    
    def create_analysis_entry(self, user_id:str, analysis_name: str, start_date: datetime) -> str:
        timestamp = datetime.now()
        analysis_id = db.execute_fetch_and_commit(
            "INSERT INTO analysis_history (analysis_name, creation_timestamp, prediction_start_date, user_id) VALUES (%s, %s, %s, %s) RETURNING id",
            analysis_name, timestamp, start_date, user_id
            )
        return analysis_id
        
    def save_file_info(self, filenames:list, analysis_id: str) -> None:
        for file in filenames:
            db.execute_and_commit(
                "INSERT INTO analysis_uploads (dataset_file_name, analysis_id) VALUES (%s, %s)",
                file, analysis_id 
            )

    def save_prediction_values(self, analysis_id, predictions, region_id_map) -> None:
        rows = []
        for region, values in predictions.items():
            for i, value in enumerate(values):
                rows.append((i + 1, round(value, 3), analysis_id, region_id_map[region]))
        
        db.execute_many_and_commit(
            "INSERT INTO predictions(month_index, prediction_val, analysis_id, region_id) VALUES (%s, %s, %s, %s)",
            rows
        )

    def save_analysis_stats(self, analysis_id, stats, region_id_map) -> None:
        rows = []
        for region, values in stats.items():
            rows.append((round(values['rmse'], 3), round(values['mean_bias'], 3), round(values['pearson_corr'], 3), analysis_id, region_id_map[region]))
        
        db.execute_many_and_commit(
            "INSERT INTO analysis_stats(rmse_val, mean_bias_val, pearson_corr_val, analysis_id, region_id) VALUES (%s, %s, %s, %s, %s)",
            rows
        )

    def save_analysis_errors(self, analysis_id, errors, region_id_map) -> None:
        rows = []
        for region, values in errors.items():
            for i, value in enumerate(values):
                rows.append((i + 1, round(value, 3), analysis_id, region_id_map[region]))
        
        db.execute_many_and_commit(
            "INSERT INTO analysis_errors(month_index, error_val, analysis_id, region_id) VALUES (%s, %s, %s, %s)",
            rows
        )

    def get_user_analyses(self, user_id) -> list:
        analyses = db.execute_and_fetch_all("SELECT * FROM analysis_history WHERE user_id = %s",
                                            user_id)
        
        return analyses
    
    def get_analysis_values(self, analysis_id):
        predictions = defaultdict(list)
        preds_result = db.execute_and_fetch_all(
                "SELECT r.region, p.id, p.month_index, p.prediction_val, p.analysis_id, p.region_id \
                FROM predictions p \
                INNER JOIN regions r \
                ON r.id = p.region_id \
                WHERE p.analysis_id = %s \
                ORDER BY p.region_id, p.month_index",
                analysis_id
            )
        
        errors = defaultdict(list)
        errors_result = db.execute_and_fetch_all(
                "SELECT r.region, e.id, e.month_index, e.error_val, e.analysis_id, e.region_id \
                FROM analysis_errors e \
                INNER JOIN regions r \
                ON r.id = e.region_id \
                WHERE e.analysis_id = %s \
                ORDER BY e.region_id, e.month_index",
                analysis_id
            )
        
        stats = {}
        stats_result = db.execute_and_fetch_all(
                "SELECT r.region, s.id, s.rmse_val, s.mean_bias_val, s.pearson_corr_val, s.region_id \
                FROM analysis_stats s \
                INNER JOIN regions r \
                ON r.id = s.region_id \
                WHERE s.analysis_id = %s",
                analysis_id
            )
        
        prediction_start_date_result = db.execute_and_fetch_one(
            "SELECT prediction_start_date FROM analysis_history \
            WHERE id = %s \
            LIMIT 1;",
            analysis_id
        )

        prediction_start_date = prediction_start_date_result[0]
        print(prediction_start_date)
        
        for pred in preds_result:
            predictions[pred[0]].append(float(pred[3]))

        for error in errors_result:
            errors[error[0]].append(float(error[3]))

        for stat in stats_result:
            stats[stat[0]] = {
                'rmse': float(stat[2]),
                'mean_bias': float(stat[3]),
                'pearson_corr': float(stat[4])
            }
        
        return predictions, stats, errors, prediction_start_date
    
    def delete_analysis(self, analysis_ids:list) -> None:
        analyses_tuple = tuple(analysis_ids)

        db.execute_and_commit("DELETE FROM predictions WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_uploads WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_history WHERE id IN %s", analyses_tuple)

    def delete_all_analyses(self, user_id) -> None:
        analyses = db.execute_and_fetch_all("SELECT id FROM analysis_history WHERE user_id = %s", user_id)
        analyses_tuple = tuple(analysis[0] for analysis in analyses)

        db.execute_and_commit("DELETE FROM predictions WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_errors WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_stats WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_uploads WHERE analysis_id IN %s", analyses_tuple)
        db.execute_and_commit("DELETE FROM analysis_history WHERE id IN %s", analyses_tuple)