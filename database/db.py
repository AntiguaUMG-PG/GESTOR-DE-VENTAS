import psycopg2

def conexion_sql():
    """Función para la configuración de la conexión a PostgreSQL"""
    try:
        # Configuración de conexión a PostgreSQL
        connection = psycopg2.connect(
            host="dpg-d3pcushr0fns73ahqf10-a.oregon-postgres.render.com", 
            port=5432,
            database="gestor_pedidos",
            user="manager_sebaot",
            password="ovRHNzwztDohjnzPWt70QwLxBwf7bEAc"
        )
        print("✅ Conexión exitosa a PostgreSQL")
        return connection
        
    except Exception as error:
        print(f"❌ Error de conexión a PostgreSQL: {str(error)}")
        return None