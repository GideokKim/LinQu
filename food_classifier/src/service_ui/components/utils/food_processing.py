import os
import sys
import io

# Add the parent directory to the system path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(parent_dir)

from clients.ml_communicator import MLCommunicator
from clients.db_client import DatabaseClient

class FoodProcessor:
    def __init__(self, ml_communicator=None, db_client=None):
        self.ml_communicator = ml_communicator or MLCommunicator()
        self.db_client = db_client or DatabaseClient()
    
    def get_nutritional_info(self, image, session_state):
        """
        Process food image and get nutritional information
        """
        if image is None:
            return {
                'error': "No image captured",
                'food_info': None,
                'confidence': 0
            }
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            # Get food prediction
            food_name, confidence = self.ml_communicator.get_food_prediction(img_bytes)
            
            # Get nutritional information
            self.db_client.connect()
            food_info = self.db_client.get_food_info_from_db(food_name)
            
            if food_info and session_state.is_active():
                # Record food consumption
                success = self.db_client.record_food_consumption(
                    customer_id=session_state.customer_id,
                    food_id=food_info['food_id']
                )
                if not success:
                    print(f"Failed to record food consumption for food_id: {food_info['food_id']}")
            
            self.db_client.close()
            
            if not food_info:
                return {
                    'error': f"No nutritional information found for {food_name}.",
                    'food_info': None,
                    'confidence': confidence
                }
            
            return {
                'error': None,
                'food_info': food_info,
                'confidence': confidence
            }
            
        except Exception as e:
            return {
                'error': f"Error: {str(e)}",
                'food_info': None,
                'confidence': 0
            }

    def get_recommended_values(self, session_state):
        """
        Get recommended nutritional values for the current customer
        """
        try:
            if not session_state.is_active():
                print("No active customer session")
                return None
                
            self.db_client.connect()
            recommended = self.db_client.get_recommended_nutrition(session_state.customer_id)
            
            if recommended:
                return {
                    'calories': recommended['Energy_max'],
                    'carbohydrates': recommended['Carbohydrates_max'],
                    'protein': recommended['Protein_max'],
                    'fat': recommended['Fat_max'],
                    'fiber': recommended['Dietary_Fiber_max'],
                    'sodium': recommended['Sodium_max']
                }
            return None
            
        except Exception as e:
            print(f"Error getting recommended values: {str(e)}")
            return None
        finally:
            self.db_client.close() 