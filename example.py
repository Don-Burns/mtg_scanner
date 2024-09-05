def __module_private_func() -> None:
    pass


class MyClass:
    def __init__(self) -> None:

        __module_private_func()


def main() -> int:
    """
    Main function
    """
    __module_private_func()
    MyClass()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
