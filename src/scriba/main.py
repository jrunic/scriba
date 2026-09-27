"""CLI scriba — montagem do app Typer."""

import typer

from scriba import __version__
from scriba.commands import auth_cmd, cal_cmd, mail_cmd


def _version_callback(value: bool) -> None:
    if value:
        print(f"scriba {__version__}")
        raise typer.Exit()


app = typer.Typer(help="CLI para Microsoft Graph — e-mail e agenda delegados.")
app.add_typer(auth_cmd.app, name="auth", help="Comandos de autenticação")
app.add_typer(mail_cmd.app, name="mail", help="Comandos de e-mail")
app.add_typer(cal_cmd.app, name="cal", help="Comandos de agenda")


@app.callback()
def main(
    version: bool = typer.Option(None, "--version", callback=_version_callback, is_eager=True),
) -> None:
    pass
