import logging
from logging.config import fileConfig
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:  # pragma: no cover
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_offline(db, configure_options):  # pragma: no cover
    """Run migrations in 'offline' mode."""
    # for the --sql use case, run migrations for each URL into
    # individual files.

    db_names = []
    for name in db.metadatas:
        if db.get_engine(name) is None:
            continue
        db_names.append(name or "")

        print_name = name
        if print_name is None:
            print_name = "default"
            while print_name in db.metadatas:
                print_name = "_" + print_name

        logger.info("Migrating database %s" % print_name)
        file_ = "%s.sql" % print_name
        logger.info("Writing output to %s" % file_)
        with open(file_, "w") as buffer:
            context.configure(
                url=db.get_engine(name).url,
                output_buffer=buffer,
                target_metadata=db.metadatas.get(name),
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
                **configure_options,
            )
            with context.begin_transaction():
                context.run_migrations(engine_name=name or "")

    config.set_main_option("databases", ",".join(db_names))


def get_engines(db):
    engines = {}
    for name in db.metadatas:
        engine = db.get_engine(name)
        if engine is None:  # pragma: no cover
            continue

        print_name = name
        if print_name is None:
            print_name = "[default]"

        rec = {"print_name": print_name, "engine": engine}
        engines[name] = rec
    return engines


def do_run_migrations_online(connection, metadata, name, configure_options):
    context.configure(
        connection=connection,
        upgrade_token="%s_upgrades" % (name or ""),
        downgrade_token="%s_downgrades" % (name or ""),
        target_metadata=metadata,
        **configure_options,
    )
    context.run_migrations(engine_name=name or "")


def run_migrations_online(db, configure_options):
    """Run migrations in 'online' mode."""
    engines = get_engines(db)
    config.set_main_option("databases", ",".join(
        [name or "" for name in engines.keys()]))

    for rec in engines.values():
        rec["connection"] = rec["engine"].connect()
        rec["transaction"] = rec["connection"].begin()

    try:
        for name, rec in engines.items():
            logger.info("Migrating database %s" % rec["print_name"])
            do_run_migrations_online(
                rec["connection"], db.metadatas.get(name), name,
                configure_options)
        for rec in engines.values():
            rec["transaction"].commit()
    except:  # noqa: E722  # pragma: no cover
        for rec in engines.values():
            rec["transaction"].rollback()
        raise
    finally:
        for rec in engines.values():
            rec["connection"].close()


async def run_migrations_async(db, configure_options):
    """Run migrations in 'online' mode."""
    engines = get_engines(db)
    config.set_main_option("databases", ",".join(
        [name or "" for name in engines.keys()]))

    for rec in engines.values():
        rec["connection"] = rec["engine"].connect()
        await rec["connection"].start()
        rec["transaction"] = rec["connection"].begin()
        await rec["transaction"].start()

    try:
        for name, rec in engines.items():
            logger.info("Migrating database %s" % rec["print_name"])
            await rec["connection"].run_sync(
                do_run_migrations_online, db.metadatas.get(name), name,
                configure_options)
        for rec in engines.values():
            await rec["transaction"].commit()
    except:  # noqa: E722  # pragma: no cover
        for rec in engines.values():
            await rec["transaction"].rollback()
        raise
    finally:
        for rec in engines.values():
            await rec["connection"].close()


def run_migrations(db, configure_options=None):
    """Run migrations."""
    if context.is_offline_mode():
        run_migrations_offline(db, configure_options or {})  # pragma: no cover
    elif not db.is_async():
        run_migrations_online(db, configure_options or {})
    else:
        import asyncio
        asyncio.run(run_migrations_async(db, configure_options or {}))
