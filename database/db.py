import psycopg2

def conexion_sql():
    """Función para la configuración de la conexión a PostgreSQL"""
    try:
        # Configuración de conexión a PostgreSQL
        connection = psycopg2.connect(
            host="dpg-da2675e1egvs739cgi7g-a.oregon-postgres.render.com", 
            port=5432,
            database="gestor_pedidos",
            user="manager_sebaot",
            password="onNqKFOhI0rDgDPTQee94dE6WHOKfAXC"
        )
        print("✅ Conexión exitosa a PostgreSQL")
        return connection
        
    except Exception as error:
        print(f"❌ Error de conexión a PostgreSQL: {str(error)}")
        return None