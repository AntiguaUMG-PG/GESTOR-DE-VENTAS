import psycopg2

def conexion_sql():
    """Función para la configuración de la conexión a PostgreSQL"""
    try:
        # Configuración de conexión a PostgreSQL
        connection = psycopg2.connect(
            host="LENOVONATHA", 
            port=5432,
            database="gestor_pedidos",
            user="postgres",
            password=""
        )
        print("✅ Conexión exitosa a PostgreSQL")
        return connection
        
    except Exception as error:
        print(f"❌ Error de conexión a PostgreSQL: {str(error)}")
        return None