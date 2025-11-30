import os
import pandas as pd
import xgboost as xgb
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from io import StringIO
import shap

app = FastAPI()

# Папка для статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

MODEL_PATH = "xgboost_model.json"
IMAGE_PATH = "SHAP.png"
UPLOADED_CSV_PATH = "uploaded_data.csv"

# Загружаем модель XGBoost
def load_model():
    model = xgb.Booster()
    model.load_model(MODEL_PATH)
    return model

# 2. Функция для обработки и предсказания данных
def predict_with_model(df: pd.DataFrame, model: xgb.Booster):
    # Преобразуем DataFrame в DMatrix, который требуется для XGBoost
    dmatrix = xgb.DMatrix(df)
    # Получаем предсказания
    predictions = model.predict(dmatrix)
    df['target'] = predictions  # Добавляем предсказанный столбец 'target'
    return df

# Эндпоинт для получения изображения info.png
@app.get("/info_image/")
def get_info_image():
    return FileResponse(IMAGE_PATH, media_type="image/png")

# 4. Эндпоинт для загрузки .csv и обработки данных
@app.post("/upload_csv/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # Чтение CSV файла в DataFrame
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode('utf-8')))  # Преобразуем в DataFrame
        df = df.iloc[:,2:]
        
        # Загружаем модель
        model = xgb.Booster()
        model.load_model(MODEL_PATH)

        #Подготовка признаков для теста (без 'target' и 'w')
        X_test = df.drop(columns=["target", "w"], errors="ignore")
        
        # Создание DMatrix для теста
        dtest = xgb.DMatrix(X_test)
        predictions = model.predict(dtest)
        df['target'] = predictions
        df['PDN'] = df['hdb_outstand_sum'] / df['incomeValue']*100
        
        # Сохраняем обновленный DataFrame на сервере
        df.to_csv(UPLOADED_CSV_PATH, index=False, encoding='utf-8')
        
        return {"message": "File processed successfully", "data": df.head().to_dict(orient="records")}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# 5. Эндпоинт для получения информации о пользователе по ID
@app.get("/user/{user_id}/")
async def get_user_info(user_id: int, fields: str):
    try:
        # Чтение сохраненного DataFrame
        df = pd.read_csv(UPLOADED_CSV_PATH, encoding='utf-8')
        
        # Ищем пользователя по ID
        user = df[df['id'] == user_id]
        
        if user.empty:
            raise HTTPException(status_code=404, detail="User not found")

        # Возвращаем только указанные поля
        user_info = user[['id', 'target', 'incomeValue', 'avg_cur_cr_turn', 'ovrd_sum', 'PDN']].to_dict(orient="records")
        return {"user_info": user_info}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user info: {str(e)}")

# Эндпоинт для отображения главной страницы (index.html)
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r") as f:
        return f.read()
