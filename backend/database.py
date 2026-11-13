from mysql.connector import connect
from .config import DB_CONFIG


def get_connection():
    return connect(**DB_CONFIG)


def initialize_database():
    tables = [

        """
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_name VARCHAR(100) NOT NULL UNIQUE,
            priority INT DEFAULT 100
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id INT AUTO_INCREMENT PRIMARY KEY,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            status VARCHAR(30) DEFAULT 'RUNNING',
            input_rows INT DEFAULT 0,
            accepted_rows INT DEFAULT 0,
            rejected_rows INT DEFAULT 0,
            duplicate_rows INT DEFAULT 0,
            output_rows INT DEFAULT 0,
            error_message TEXT
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            identity_key VARCHAR(255) NOT NULL UNIQUE,
            gtin VARCHAR(30),
            name VARCHAR(255),
            brand VARCHAR(255),
            category VARCHAR(255),
            price DECIMAL(12,2),
            currency VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS product_sources (
            source_id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            supplier_id INT NOT NULL,
            supplier_sku VARCHAR(150),
            source_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_source (supplier_id, supplier_sku),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS attribute_provenance (
            provenance_id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            attribute_name VARCHAR(100) NOT NULL,
            supplier_id INT NOT NULL,
            attribute_value JSON,
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
            UNIQUE KEY unique_attribute (product_id, attribute_name)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS rejected_records (
            reject_id INT AUTO_INCREMENT PRIMARY KEY,
            run_id INT,
            supplier_name VARCHAR(100),
            source_data JSON,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
        )
        """
    ]

    connection = get_connection()
    cursor = connection.cursor()

    try:
        for table_sql in tables:
            cursor.execute(table_sql)

        connection.commit()
        print("All database tables created successfully!")

    finally:
        cursor.close()
        connection.close()