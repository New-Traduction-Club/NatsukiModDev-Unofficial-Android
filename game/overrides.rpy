python early:
    def dummy(*args, **kwargs):
        """
        Dummy function. Does absolutely nothing
        """
        return

    renpy.execution.check_infinite_loop = dummy

    import renpy.sl2.slparser as slparser
    if "at" not in slparser.screen_parser.keyword:
        slparser.screen_parser.keyword["at"] = slparser.Keyword("at")

