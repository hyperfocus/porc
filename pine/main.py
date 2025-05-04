import typer

app = typer.Typer()

@app.command()
def cli():
    print("PINE CLI initialized")

if __name__ == "__main__":
    app()
