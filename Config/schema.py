"""Creación de tablas y migración del esquema al iniciar la aplicación.

`db.create_all()` crea las tablas que faltan, pero no agrega columnas a tablas que ya
existen. Para bases MySQL creadas con versiones anteriores del proyecto, este módulo
agrega las columnas, índices y llaves foráneas que faltan y enlaza los datos antiguos
(que guardaban nombres en texto) con las filas correspondientes. Es idempotente:
se puede ejecutar en cada arranque. Usa information_schema, por eso solo corre en MySQL.
"""

from sqlalchemy import inspect, text

from Config.db import app, db


def _run(sql):
    """Ejecuta una sentencia; si falla (p. ej. ya existe) se ignora y se hace rollback."""
    try:
        db.session.execute(text(sql))
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.debug("Sentencia omitida: %s", sql)


def _scalar(sql, **params):
    return db.session.execute(text(sql), params).scalar() or 0


def _columns(table):
    return {c["name"]: c for c in inspect(db.engine).get_columns(table)}


def _add_column(table, column, ddl):
    if column not in _columns(table):
        _run(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _add_index(table, name, columns, unique=False):
    exists = _scalar(
        """
        SELECT COUNT(1) FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = :t AND index_name = :n
        """,
        t=table, n=name,
    )
    if not exists:
        _run(f"CREATE {'UNIQUE ' if unique else ''}INDEX {name} ON {table}({columns})")


def _add_fk(table, name, column, ref_table, on_delete="SET NULL"):
    # Se busca cualquier FK sobre la columna (no solo por nombre): en bases nuevas
    # create_all ya las crea con nombres automáticos como mascotas_ibfk_1.
    exists = _scalar(
        """
        SELECT COUNT(1) FROM information_schema.KEY_COLUMN_USAGE
        WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c
          AND referenced_table_name = :r
        """,
        t=table, c=column, r=ref_table,
    )
    if not exists:
        _run(
            f"ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) "
            f"REFERENCES {ref_table}(id) ON UPDATE CASCADE ON DELETE {on_delete}"
        )


def _make_nullable(table, column, ddl):
    col = _columns(table).get(column)
    if col and not col.get("nullable", True):
        _run(f"ALTER TABLE {table} MODIFY COLUMN {column} {ddl} NULL")


def migrate_adoptar_mascotas():
    """Solicitudes de adopción -> usuarios (adoptante) y mascotas (mascota pedida)."""
    required = [
        ("telefono", "VARCHAR(30) NULL"),
        ("direccion", "VARCHAR(200) NULL"),
        ("ocupacion", "VARCHAR(100) NULL"),
        ("vivienda", "VARCHAR(80) NULL"),
        ("tiene_mascotas", "VARCHAR(80) NULL"),
        ("motivo", "TEXT NULL"),
        ("pet_name", "VARCHAR(120) NULL"),
        ("adopter_id", "INT NULL"),
        ("mascota_id", "INT NULL"),
        ("is_confirmed", "TINYINT(1) NOT NULL DEFAULT 0"),
        ("created_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"),
    ]
    for column, ddl in required:
        _add_column("adoptar_mascotas", column, ddl)

    _add_index("adoptar_mascotas", "idx_adoptar_adopter_id", "adopter_id")
    _add_index("adoptar_mascotas", "idx_adoptar_mascota_id", "mascota_id")
    _add_fk("adoptar_mascotas", "fk_adoptar_usuarios", "adopter_id", "usuarios")
    _add_fk("adoptar_mascotas", "fk_adoptar_mascotas", "mascota_id", "mascotas")

    # Enlazar solicitudes antiguas con su mascota usando el nombre guardado en texto
    _run(
        """
        UPDATE adoptar_mascotas am
        JOIN mascotas m ON m.nombre = am.pet_name
        SET am.mascota_id = m.id
        WHERE am.mascota_id IS NULL
        """
    )

    # Columnas heredadas de una versión anterior de la tabla
    cols = _columns("adoptar_mascotas")
    _make_nullable("adoptar_mascotas", "password_hash", "VARCHAR(256)")
    if "updated_at" in cols:
        _run(
            "ALTER TABLE adoptar_mascotas MODIFY COLUMN updated_at DATETIME NOT NULL "
            "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )

    # 'username' no debe ser UNIQUE: una persona puede enviar varias solicitudes
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
    _add_index("adoptar_mascotas", "idx_adoptar_username", "username")


def migrate_mascotas():
    """Mascotas -> admins (quién la publicó)."""
    _add_column("mascotas", "publicado_por_id", "INT NULL")
    _add_index("mascotas", "idx_mascotas_publicado_por", "publicado_por_id")
    _add_fk("mascotas", "fk_mascotas_admins", "publicado_por_id", "admins")

    # Enlazar mascotas antiguas con el admin cuyo nombre quedó guardado en 'autor'
    _run(
        """
        UPDATE mascotas m
        JOIN admins a ON a.username = m.autor
        SET m.publicado_por_id = a.id
        WHERE m.publicado_por_id IS NULL
        """
    )


def migrate_postular_mascotas():
    """Postulaciones -> usuarios (quién la propuso) y mascotas (publicación aprobada)."""
    _add_column("postular_mascotas", "usuario_id", "INT NULL")
    _add_column("postular_mascotas", "mascota_id", "INT NULL")

    cols = _columns("postular_mascotas")
    if "email" in cols:
        # Postulaciones antiguas guardaban el email del usuario en texto
        _run(
            """
            UPDATE postular_mascotas p
            JOIN usuarios u ON u.email = p.email
            SET p.usuario_id = u.id
            WHERE p.usuario_id IS NULL
            """
        )
    if "username" in cols:
        # Antes, cada mascota publicada por un admin creaba una fila "espejo" aquí
        # (username = autor). Se enlaza con su mascota para no dejarla huérfana.
        _run(
            """
            UPDATE postular_mascotas p
            JOIN mascotas m ON m.nombre = p.nombre AND m.autor = p.username
            SET p.mascota_id = m.id
            WHERE p.mascota_id IS NULL
            """
        )

    _add_index("postular_mascotas", "idx_postular_usuario", "usuario_id")
    _add_index("postular_mascotas", "uq_postular_mascota", "mascota_id", unique=True)
    _add_fk("postular_mascotas", "fk_postular_usuarios", "usuario_id", "usuarios")
    _add_fk("postular_mascotas", "fk_postular_mascotas", "mascota_id", "mascotas")

    # Columnas heredadas que el modelo ya no usa: se dejan (conservan datos) pero opcionales
    _make_nullable("postular_mascotas", "username", "VARCHAR(80)")
    _make_nullable("postular_mascotas", "email", "VARCHAR(120)")
    _make_nullable("postular_mascotas", "password_hash", "VARCHAR(128)")


def migrate_mysql():
    insp = inspect(db.engine)
    # El orden importa: las FK necesitan que las tablas referenciadas existan
    if insp.has_table("mascotas"):
        migrate_mascotas()
    if insp.has_table("adoptar_mascotas"):
        migrate_adoptar_mascotas()
    if insp.has_table("postular_mascotas"):
        migrate_postular_mascotas()


def init_db():
    """Crea las tablas que falten y, en MySQL, migra el esquema heredado."""
    db.create_all()
    if db.engine.dialect.name == "mysql":
        try:
            migrate_mysql()
        except Exception:
            db.session.rollback()
            app.logger.exception("No se pudo migrar el esquema de la base de datos")
