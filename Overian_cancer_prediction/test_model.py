import pickle
import pandas as pd
from utils.model_utils import predict_tabular, get_default_input

def load_xgboost_model(model_path):
    try:
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
        # Assuming these are the columns based on your input data structure
        columns = ['Age', 'Menopause', 'GGT', 'HGB', 'AFP', 'CA72-4', 'ALP', 'CA19-9', 'HE4', 'CEA', 'CA125', 'Ca']
        return model, columns
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None, None

def test_prediction(input_values):
    # Load the model explicitly from the specified path
    model_path = 'xgboost_model.pkl'
    model, columns = load_xgboost_model(model_path)
    if model is None or columns is None:
        print("Failed to load model")
        return

    # Get prediction
    result = predict_tabular(model, columns, input_values)
    if result is None:
        print("Failed to get prediction")
        return

    # Print results with additional validation info
    print("\nInput Values:")
    for key, value in input_values.items():
        print(f"{key}: {value}")
    
    print("\nPrediction Results:")
    probability = result['probability']
    print(f"Raw Probability Score: {probability:.4f}")
    print(f"Cancer Probability: {probability:.2%}")
    print(f"Predicted Status: {'Likely Ovarian Cancer' if probability >= 0.5 else 'Likely No Cancer'}")
    print(f"Confidence Level: {'Very High' if probability > 0.9 else 'High' if probability > 0.7 else 'Moderate' if probability > 0.5 else 'Low'}")

def run_tests():
    # Add a control case with extremely low values
    print("\n=== Test 0: Control Case - Very Low Values ===")
    print("(Expected: Very low probability of cancer)")
    test_prediction({
        'Age': 25,
        'Menopause': 0,
        'GGT': 10,
        'HGB': 13,
        'AFP': 2,
        'CA72-4': 1,
        'ALP': 45,
        'CA19-9': 10,
        'HE4': 30,
        'CEA': 1.0,
        
        'CA125': 15,
        'Ca': 9.0
    })

    # Test 1: All normal values within reference range
    print("\n=== Test 1: Normal Values Within Reference Range ===")
    print("(Expected: Low probability of cancer - all markers normal)")
    test_prediction({
        'Age': 35,
        'Menopause': 0,
        'GGT': 25,      # Normal: 9-48 U/L
        'HGB': 14,      # Normal: 12-15.5 g/dL
        'AFP': 5,       # Normal: <10 ng/mL
        'CA72-4': 3,    # Normal: <6.9 U/mL
        'ALP': 70,      # Normal: 44-147 U/L
        'CA19-9': 30,   # Normal: <37 U/mL
        'HE4': 50,      # Normal: <140 pmol/L
        'CEA': 2.5,     # Normal: <2.5 ng/mL
        'CA125': 30,    # Normal: <35 U/mL
        'Ca': 9.5       # Normal: 8.6-10.3 mg/dL
    })

    # Test 2: Borderline values
    print("\n=== Test 2: Borderline Values ===")
    print("(Expected: Moderate risk - markers at upper limits of normal)")
    test_prediction({
        'Age': 50,
        'Menopause': 1,
        'GGT': 45,      # High normal
        'HGB': 12,      # Low normal
        'AFP': 9,       # High normal
        'CA72-4': 6,    # High normal
        'ALP': 140,     # High normal
        'CA19-9': 35,   # High normal
        'HE4': 135,     # High normal
        'CEA': 2.4,     # High normal
        'CA125': 34,    # High normal
        'Ca': 8.7       # Low normal
    })

    # Test 3: Slightly elevated markers
    print("\n=== Test 3: Slightly Elevated Values ===")
    print("(Expected: Increased risk - multiple elevated markers)")
    test_prediction({
        'Age': 55,
        'Menopause': 1,
        'GGT': 55,      # Slightly elevated
        'HGB': 11,      # Slightly low
        'AFP': 12,      # Slightly elevated
        'CA72-4': 8,    # Slightly elevated
        'ALP': 160,     # Slightly elevated
        'CA19-9': 45,   # Slightly elevated
        'HE4': 150,     # Slightly elevated
        'CEA': 3,       # Slightly elevated
        'CA125': 45,    # Slightly elevated
        'Ca': 8.4       # Slightly low
    })

    # Test 4: Significantly elevated tumor markers
    print("\n=== Test 4: Significantly Elevated Tumor Markers ===")
    print("(Expected: High risk - multiple significantly elevated markers)")
    test_prediction({
        'Age': 60,
        'Menopause': 1,
        'GGT': 70,      # Elevated
        'HGB': 110,      # Low
        'AFP': 20,      # Elevated
        'CA72-4': 15,   # Elevated
        'ALP': 200,     # Elevated
        'CA19-9': 100,  # Elevated
        'HE4': 200,     # Elevated
        'CEA': 5,       # Elevated
        'CA125': 100,   # Elevated
        'Ca': 8.0       # Low
    })
    
    # Test 5: Individual marker test - High CA125 only
    print("\n=== Test 5: High CA125 Only ===")
    print("(Expected: Moderate to high risk - CA125 significantly elevated)")
    test_prediction({
        'Age': 45,
        'Menopause': 0,
        'GGT': 30,      # Normal
        'HGB': 13,      # Normal
        'AFP': 5,       # Normal
        'CA72-4': 4,    # Normal
        'ALP': 80,      # Normal
        'CA19-9': 25,   # Normal
        'HE4': 60,      # Normal
        'CEA': 2.0,     # Normal
        'CA125': 200,   # Significantly elevated
        'Ca': 9.2       # Normal
    })

    # Add an extreme case
    print("\n=== Test 6: Extreme Values ===")
    print("(Expected: Very high risk - extremely elevated markers)")
    test_prediction({
        'Age': 65,
        'Menopause': 1,
        'GGT': 200,
        'HGB': 9,
        'AFP': 50,
        'CA72-4': 30,
        'ALP': 300,
        'CA19-9': 200,
        'HE4': 500,
        'CEA': 15,
        'CA125': 1000,
        'Ca': 7.5
    })

if __name__ == '__main__':
    run_tests()
