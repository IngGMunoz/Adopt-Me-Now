"""Creación de tablas y ajustes de esquema al iniciar la aplicación.

`adoptar_mascotas` se creó antes que el formulario actual, así que en bases de datos
existentes se agregan las columnas/índices/FK que faltan. Los ajustes usan
information_schema, por eso solo se ejecutan sobre MySQL.
"""

from sqlalchemy import inspect, text

from Config.db import app, db


def _run(sql):
    """Ejecuta una sentencia DDL; si falla (p. ej. ya existe) se ignora y se hace rollback."""
    try:
        db.session.execute(text(sql))
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.debug("DDL omitido: %s", sql)


def _scalar(sql):
    return db.session.execute(text(sql)).scalar() or 0


def ensure_adoptar_mascotas_schema():
    insp = inspect(db.engine)
    if not insp.has_table("adoptar_mascotas"):
        return

    # 1. Columnas requeridas por el formulario de adopción
    cols = {c["name"]: c for c in insp.get_columns("adoptar_mascotas")}
    required = [
        ("telefono", "VARCHAR(30) NULL"),
        ("direccion", "VARCHAR(200) NULL"),
        ("ocupacion", "VARCHAR(100) NULL"),
        ("vivienda", "VARCHAR(80) NULL"),
        ("tiene_mascotas", "VARCHAR(80) NULL"),
        ("motivo", "TEXT NULL"),
        ("pet_name", "VARCHAR(120) NULL"),
        ("adopter_id", "INT NULL"),
        ("is_confirmed", "TINYINT(1) NOT NULL DEFAULT 0"),
    ]
    for name, ddl in required:
        if name not in cols:
            _run(f"ALTER TABLE adoptar_mascotas ADD COLUMN {name} {ddl}")

    # 2. Índice y FK adopter_id -> usuarios.id
    index_exists = _scalar(
        """
        SELECT COUNT(1) FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = 'adoptar_mascotas'
          AND index_name = 'idx_adoptar_adopter_id'
        """
    )
    if not index_exists:
        _run("CREATE INDEX idx_adoptar_adopter_id ON adoptar_mascotas(adopter_id)")

    fk_exists = _scalar(
        """
        SELECT COUNT(1) FROM information_schema.REFERENTIAL_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE() AND CONSTRAINT_NAME = 'fk_adoptar_usuarios'
        """
    )
    if insp.has_table("usuarios") and not fk_exists:
        _run(
            "ALTER TABLE adoptar_mascotas ADD CONSTRAINT fk_adoptar_usuarios "
            "FOREIGN KEY (adopter_id) REFERENCES usuarios(id) "
            "ON UPDATE CASCADE ON DELETE SET NULL"
        )

    # 3. Columnas heredadas de una versión anterior de la tabla
    ph = cols.get("password_hash")
    if ph and not ph.get("nullable", True):
        _run("ALTER TABLE adoptar_mascotas MODIFY COLUMN password_hash VARCHAR(256) NULL")
    if "created_at" in cols:
        _run("ALTER TABLE adoptar_mascotas MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
    if "updated_at" in cols:
        _run(
            "ALTER TABLE adoptar_mascotas MODIFY COLUMN updated_at DATETIME NOT NULL "
            "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )

    # 4. 'username' no debe ser UNIQUE: una persona puede enviar varias solicitudes
    rows = db.session.execute(
        text(
            """
            SELECT index_name, non_unique FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND table_name = 'adoptar_mascotas'
              AND column_name = 'username'
            """
        )
    ).fetchall()
    for idx_name, non_unique in rows:
        if int(non_unique) == 0:
            _run(f"ALTER TABLE adoptar_mascotas DROP INDEX `{idx_name}`")
    remaining = _scalar(
        """
        SELECT COUNT(1) FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = 'adoptar_mascotas'
          AND column_name = 'username'
        """
    )
    if not remaining:
        _run("CREATE INDEX idx_adoptar_username ON adoptar_mascotas(username)")


def init_db():
    """Crea las tablas que falten y, en MySQL, ajusta el esquema heredado."""
    db.create_all()
    if db.engine.dialect.name == "mysql":
        try:
            ensure_adoptar_mascotas_schema()
        except Exception:
            db.session.rollback()
            app.logger.exception("No se pudo verificar el esquema de adoptar_mascotas")
