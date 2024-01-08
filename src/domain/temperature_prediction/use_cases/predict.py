import joblib
import pandas as pd


def predict_temperature(input_data):
    # Carregar o modelo treinado
    model = joblib.load('random_forest_model.pkl')

    # Convertendo os dados de entrada para o formato adequado
    input_dict = input_data.dict()
    input_dict['out/in'] = input_dict.pop('out_in')  # Ajuste para o nome correto da feature
    input_df = pd.DataFrame([input_dict])

    # Fazer a previsão
    prediction = model.predict(input_df)

    return prediction.tolist()