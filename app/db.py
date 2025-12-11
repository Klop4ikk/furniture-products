import os
import psycopg2
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# загружаем переменные окружения
load_dotenv()

class DatabaseConnection:
    """
    класс для управления подключением к PostgreSQL через SQLAlchemy
    """
    
    def __init__(self):
        # данные бд
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'postgres')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '0909')
        
        # строка для подключения SQLAlchemy (с использованием psycopg2)
        self.connection_string = (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
        
    def get_engine(self):
        """
        Создаёт и возвращает SQLAlchemy engine
        """
        try:
            engine = create_engine(self.connection_string)
            print(f"✅ SQLAlchemy engine создан для {self.database}")
            return engine
        except Exception as e:
            print(f"❌ Ошибка создания SQLAlchemy engine: {e}")
            raise
    
    def get_raw_connection(self):
        """Возвращает прямое подключение psycopg2 (для операций без pandas)"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return conn
        except Exception as e:
            print(f"❌ Ошибка прямого подключения: {e}")
            raise

db = DatabaseConnection()

def get_products():
    """
    Функция для получения всей продукции из таблицы Products_import
    """
    try:
        engine = db.get_engine()
        
        # запрос через SQLAlchemy
        query = text("""
            SELECT 
                "id" as id,
                "Product type" as product_type,
                "Product name" as name,
                "Article" as article,
                "Minimum cost for a partner" as min_price,
                "Main material" as main_material
            FROM public."Products_import"
            ORDER BY "id"
        """)
        
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
            print(f"✅ Загружено {len(df)} записей через SQLAlchemy")
            
            if not df.empty:
                print(f"\n🔍 ТИПЫ ДАННЫХ ДО ПРЕОБРАЗОВАНИЯ:")
                for col in df.columns:
                    print(f"   {col}: {df[col].dtype}")
                    if col == 'min_price':
                        print(f"     Пример значений: {df[col].head().tolist()}")
                
                # id -> int
                if 'id' in df.columns:
                    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
                
                # article -> int
                if 'article' in df.columns:
                    df['article'] = pd.to_numeric(df['article'], errors='coerce').fillna(0).astype(int)
                
                # min_price -> float
                if 'min_price' in df.columns:
                    original_values = df['min_price'].copy()
                    df['min_price'] = pd.to_numeric(df['min_price'], errors='coerce')
                    
                    nan_count = df['min_price'].isna().sum()
                    if nan_count > 0:
                        print(f"     ⚠️ {nan_count} значений не удалось преобразовать напрямую")
                        
                        for idx in df[df['min_price'].isna()].index:
                            original_val = original_values[idx]
                            if isinstance(original_val, str):
                                clean_val = ''.join(c for c in original_val if c.isdigit() or c in '.-')
                                if clean_val:
                                    try:
                                        df.loc[idx, 'min_price'] = float(clean_val)
                                        print(f"       Строка {idx}: '{original_val}' -> {clean_val} -> {float(clean_val)}")
                                    except:
                                        df.loc[idx, 'min_price'] = 0.0
                                        print(f"       Строка {idx}: '{original_val}' -> 0.0 (ошибка преобразования)")
                    
                    df['min_price'] = df['min_price'].fillna(0.0)
                    print(f"   ✅ min_price: преобразовано в float, NaN заменены на 0.0")
                    
                    print(f"     Тип после преобразования: {df['min_price'].dtype}")
                    print(f"     Пример значений после: {df['min_price'].head().tolist()}")
                
                print(f"\n📊 ИТОГОВЫЕ ТИПЫ ДАННЫХ:")
                for col in df.columns:
                    print(f"   {col}: {df[col].dtype}")
                
                print(f"\n📝 ПЕРВЫЕ 3 СТРОКИ ДАННЫХ:")
                print(df.head(3).to_string())
            
            return df
            
    except SQLAlchemyError as e:
        print(f"❌ Ошибка SQLAlchemy: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return pd.DataFrame()

def get_product_by_id(product_id):
    """
    Функция для получения данных о конкретном продукте по ID
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM public."Products_import" WHERE "id" = %s', (product_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            return dict(zip(columns, row))
        return None
        
    except Exception as e:
        print(f"Ошибка при загрузке продукта {product_id}: {e}")
        return None

def add_product(product_data):
    """
    добавление нового продукта
    """
    try:
        next_id = get_next_product_id()
        
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO public."Products_import" 
        ("id", "Product type", "Product name", "Article", 
         "Minimum cost for a partner", "Main material")
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING "id"
        """
        
        cursor.execute(query, (
            next_id,
            product_data['product_type'],
            product_data['name'],
            product_data['article'],
            product_data['min_price'],
            product_data['main_material']
        ))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Продукт добавлен с ID: {new_id}")
        return new_id
        
    except Exception as e:
        try:
            print("🔄 Пробуем добавить без указания ID...")
            conn = db.get_raw_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO public."Products_import" 
            ("Product type", "Product name", "Article", 
             "Minimum cost for a partner", "Main material")
            VALUES (%s, %s, %s, %s, %s)
            RETURNING "id"
            """
            
            cursor.execute(query, (
                product_data['product_type'],
                product_data['name'],
                product_data['article'],
                product_data['min_price'],
                product_data['main_material']
            ))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print(f"✅ Продукт добавлен с ID: {new_id} (автоматически)")
            return new_id
            
        except Exception as e2:
            print(f"❌ Ошибка при повторной попытке: {e2}")
            raise

def update_product(product_id, product_data):
    """
    Обновление данных существующего продукта
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = """
        UPDATE public."Products_import" 
        SET "Product type" = %s, "Product name" = %s, "Article" = %s,
            "Minimum cost for a partner" = %s, "Main material" = %s
        WHERE "id" = %s
        """
        
        cursor.execute(query, (
            product_data['product_type'],
            product_data['name'],
            product_data['article'],
            product_data['min_price'],
            product_data['main_material'],
            product_id
        ))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Продукт {product_id} обновлен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении продукта {product_id}: {e}")
        raise

def delete_product(product_id):
    """Удаляет продукт по ID"""
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM public."Products_import" WHERE "id" = %s'
        cursor.execute(query, (product_id,))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Продукт {product_id} удален")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении продукта {product_id}: {e}")
        raise

def get_workshops():
    """Получает список всех цехов"""
    try:
        engine = db.get_engine()
        
        query = text("""
            SELECT 
                "id" as id,
                "Workshop name" as name,
                "Number of people for production" as employee_count
            FROM public."Workshops_import"
            ORDER BY "id"
        """)
        
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
            
            if not df.empty and 'employee_count' in df.columns:
                df['employee_count'] = pd.to_numeric(df['employee_count'], errors='coerce').fillna(0).astype(int)
            
            return df
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке цехов: {e}")
        return pd.DataFrame()

def get_product_types():
    """
    Получение типов продукции и коэффициенты
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            "id" as id,
            "Product type" as name,
            "Product type coefficient" as coefficient
        FROM public."Product_type_import"
        ORDER BY "id"
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            if 'coefficient' in row_dict:
                try:
                    row_dict['coefficient'] = float(row_dict['coefficient'])
                except:
                    row_dict['coefficient'] = 1.0
            result.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке типов продукции: {e}")
        return []

def get_material_types():
    """
    Получение типов материалов и процентов потерь
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            "id" as id,
            "Type material" as name,
            "Percentage of raw material losses" as loss_percent
        FROM public."Material_type_import"
        ORDER BY "id"
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            if 'loss_percent' in row_dict:
                try:
                    row_dict['loss_percent'] = float(row_dict['loss_percent'])
                except:
                    row_dict['loss_percent'] = 0.0
            result.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке типов материалов: {e}")
        return []

def get_unique_product_types():
    """
    Получение уникальных типов продукции для фильтров
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = 'SELECT DISTINCT "Product type" FROM public."Products_import"'
        cursor.execute(query)
        
        result = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке уникальных типов: {e}")
        return []

def get_unique_materials():
    """
    Полученипе уникальных материалов для фильтров
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = 'SELECT DISTINCT "Main material" FROM public."Products_import"'
        cursor.execute(query)
        
        result = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке уникальных материалов: {e}")
        return []

def get_next_product_id():
    """
    Получение корректьного айди для нового продукта
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX("id") FROM public."Products_import"')
        result = cursor.fetchone()
        
        max_id = result[0] if result[0] is not None else 0
        
        cursor.close()
        conn.close()
        
        next_id = max_id + 1
        print(f"📈 Следующий доступный ID: {next_id} (максимальный: {max_id})")
        return next_id
        
    except Exception as e:
        print(f"❌ Ошибка при получении следующего ID: {e}")
        return 1

def get_production_time_for_product(product_name):
    """
    получение общего времени производства для продукта
    (сумма времени из всех связанных цехов)
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT SUM("Production time, h") as total_time
        FROM public."Product_workshops_import"
        WHERE "Product name" = %s
        """
        
        cursor.execute(query, (product_name,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        total_time = result[0] if result[0] is not None else 0
        print(f"⏱️ Время производства для '{product_name}': {total_time} ч.")
        return total_time
        
    except Exception as e:
        print(f"❌ Ошибка при получении времени производства: {e}")
        return 0

def get_products_with_production_time():
    """
    Получение списка продукции с рассчитанным временем производства
    """
    try:
        products_df = get_products()
        
        if products_df.empty:
            return pd.DataFrame()
        
        production_times = []
        for _, product in products_df.iterrows():
            product_name = product['name']
            total_time = get_production_time_for_product(product_name)
            production_times.append(total_time)
        
        products_df['production_time_h'] = production_times
        return products_df
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке продуктов с временем производства: {e}")
        return pd.DataFrame()

def get_available_workshops():
    """
    Получение списка всех доступных цехов
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = 'SELECT DISTINCT "Workshop name" FROM public."Workshops_import" ORDER BY "Workshop name"'
        cursor.execute(query)
        
        result = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        print(f"🏭 Доступные цехи: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка цехов: {e}")
        return []

def add_production_time(product_name, workshop_name, production_time):
    """
    Добавление времени производства продукта в цехе
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX("id") FROM public."Product_workshops_import"')
        result = cursor.fetchone()
        next_id = result[0] + 1 if result[0] is not None else 1
        
        query = """
        INSERT INTO public."Product_workshops_import" 
        ("id", "Product name", "Workshop name", "Production time, h")
        VALUES (%s, %s, %s, %s)
        RETURNING "id"
        """
        
        cursor.execute(query, (next_id, product_name, workshop_name, production_time))
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Добавлено время производства: {product_name} в цехе {workshop_name} - {production_time} ч. (ID: {new_id})")
        return new_id
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении времени производства: {e}")
        raise

def get_production_times_for_product(product_name):
    """
    Получаем все записи о времени производства для конкретного продукта
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            "id" as id,
            "Product name" as product_name,
            "Workshop name" as workshop_name,
            "Production time, h" as production_time
        FROM public."Product_workshops_import"
        WHERE "Product name" = %s
        ORDER BY "id"
        """
        
        cursor.execute(query, (product_name,))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        
        print(f"📊 Записи времени производства для '{product_name}': {len(result)}")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при получении времени производства: {e}")
        return []

def delete_production_time(record_id):
    """
    удаление записи о времени производства по айдишнику
    """
    try:
        conn = db.get_raw_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM public."Product_workshops_import" WHERE "id" = %s'
        cursor.execute(query, (record_id,))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Удалена запись времени производства с ID: {record_id}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении времени производства: {e}")
        raise
