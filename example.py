def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"


def main() -> None:
    """Run a simple demonstration of the greet function."""
    print(greet("world"))


if __name__ == "__main__":
    main()
