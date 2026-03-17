"""CLI entry point"""

import argparse
import os
import sys

from alembic import command
from axion_lab_server.shared.kernel.migrations import create_alembic_config


def _run_alembic_command(args: list[str]) -> None:
    config = create_alembic_config()

    if not args:
        raise ValueError("No Alembic command provided")

    if args[0] == "upgrade":
        if len(args) != 2:
            raise ValueError("upgrade expects a single revision target")
        command.upgrade(config, args[1])
        return

    if args[0] == "downgrade":
        if len(args) != 2:
            raise ValueError("downgrade expects a single revision target")
        command.downgrade(config, args[1])
        return

    if args[0] == "revision":
        autogenerate = False
        message: str | None = None
        index = 1

        while index < len(args):
            arg = args[index]
            if arg in {"-a", "--autogenerate"}:
                autogenerate = True
                index += 1
                continue

            if arg in {"-m", "--message"}:
                if index + 1 >= len(args):
                    raise ValueError("revision requires a message after -m/--message")
                message = args[index + 1]
                index += 2
                continue

            raise ValueError(f"Unsupported Alembic revision argument: {arg}")

        if message is None:
            raise ValueError("revision requires -m/--message")

        command.revision(config, message=message, autogenerate=autogenerate)
        return

    raise ValueError(f"Unsupported Alembic command: {args[0]}")


def main() -> None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Axion Lab - Artifact-first Experiment Evaluation System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    server_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    server_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    server_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    # DB commands
    subparsers.add_parser(
        "db-upgrade", help="Run database migrations (alembic upgrade head)"
    )
    subparsers.add_parser("db-downgrade", help="Downgrade database by one revision")

    # Migration command
    migrate_parser = subparsers.add_parser("db-migrate", help="Create a new migration")
    migrate_parser.add_argument("message", help="Migration message")
    migrate_parser.add_argument(
        "--autogenerate",
        "-a",
        action="store_true",
        help="Autogenerate migration from models",
    )

    args = parser.parse_args()

    if args.command == "server":
        run_server(args.host, args.port, args.reload)
    elif args.command == "db-upgrade":
        run_alembic(["upgrade", "head"])
    elif args.command == "db-downgrade":
        run_alembic(["downgrade", "-1"])
    elif args.command == "db-migrate":
        cmd = ["revision", "-m", args.message]
        if args.autogenerate:
            cmd.append("--autogenerate")
        run_alembic(cmd)
    else:
        parser.print_help()
        sys.exit(1)


def run_server(host: str, port: int, reload: bool) -> None:
    """Run the API server."""
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./axion_lab.db")
    os.environ.setdefault("DATABASE_TYPE", "sqlite")
    os.environ.setdefault("OBJECT_STORE_PROVIDER", "file")
    os.environ.setdefault("OBJECT_STORE_LOCAL_PATH", "./data/object_store")

    import uvicorn

    uvicorn.run(
        "axion_lab_server.apps.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


def run_alembic(args: list[str], *, exit_after: bool = True) -> int:
    """Run alembic command"""
    _run_alembic_command(args)
    if exit_after:
        sys.exit(0)
    return 0


if __name__ == "__main__":
    main()
