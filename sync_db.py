from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.schema import CreateTable

class CustomSchemaSynchronizer:
    """
    Класс для синхронизации схемы БД по образцу тестовой.
    """
    def __init__(self, test_db_url: str, prod_db_url: str):
        self.test_engine = create_engine(test_db_url)
        self.prod_engine = create_engine(prod_db_url)

    def generate_diff(self) -> list:
        """Анализирует базы и возвращает список SQL-запросов для миграции."""
        test_meta = MetaData()
        test_meta.reflect(bind=self.test_engine)
        
        prod_meta = MetaData()
        prod_meta.reflect(bind=self.prod_engine)
        
        queries = []
        
        # test_meta.sorted_tables вместо test_meta.tables.items()
        for test_table in test_meta.sorted_tables:
            table_name = test_table.name # имя из объекта таблицы
            
            if table_name not in prod_meta.tables:
                create_sql = str(CreateTable(test_table).compile(dialect=self.prod_engine.dialect)).strip()
                if not create_sql.endswith(';'):
                    create_sql += ';'
                queries.append(create_sql)
            else:
                prod_table = prod_meta.tables[table_name]
                for col in test_table.columns:
                    if col.name not in prod_table.columns:
                        col_type = str(col.type.compile(dialect=self.prod_engine.dialect))
                        
                        default_clause = ""
                        if col.server_default is not None:
                            default_clause = f" DEFAULT {col.server_default.arg}"
                        
                        queries.append(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause};")
                        
        return queries
            

    def apply_changes(self):
        """Интерактивно применяет изменения к боевой базе."""
        try:
            queries = self.generate_diff()
            if not queries:
                print("Схемы баз данных идентичны. Обновление не требуется.")
                return

            print("Следующие SQL-запросы будут выполнены на боевой БД:\n")
            print("-" * 50)
            for q in queries:
                print(q)
            print("-" * 50)
            
            confirm = input("\nВы уверены, что хотите применить эти изменения на ПРОД? (y/n): ")
            if confirm.lower() == 'y':
                with self.prod_engine.begin() as conn:
                    for q in queries:
                        conn.execute(text(q))
                print("✅ Изменения успешно применены к боевой базе.")
            else:
                print("Операция прервана пользователем.")
                
        except Exception as e:
            print(f"Ошибка при синхронизации: {e}")

if __name__ == "__main__":
    TEST_DB_URL = "postgresql://admin:secretpassword@localhost:5433/test_database"
    PROD_DB_URL = "postgresql://admin:secretpassword@localhost:5432/prod_database"

    synchronizer = CustomSchemaSynchronizer(test_db_url=TEST_DB_URL, prod_db_url=PROD_DB_URL)
    synchronizer.apply_changes()
