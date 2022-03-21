from cli_skeleton.core.exceptions import CLISkeletonExceptions


def test_print(test):
    try:
        print(test)
    except Exception as err:
        raise CLISkeletonExceptions(str(err))

    else:
        print("Success")