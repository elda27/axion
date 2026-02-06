"""CLI entry point"""

import argparse
import subprocess
import sys


def main() -> None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Axion - Artifact-first Experiment Evaluation System"
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
    """Run the API server"""
    import uvicorn

    uvicorn.run(
        "axion_server.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


def run_alembic(args: list[str]) -> None:
    """Run alembic command"""
    result = subprocess.run(["alembic"] + args, check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
