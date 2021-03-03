










class Parameters:
    fields: dict[str, str]
    function: str
    level: dict[str, float]
    path: str
    source: str
    meta: dict[str, Any]

    def __init__(self, path: str, *, function: str = FUNCTION, source: str = SOURCE, 
                 fields: D = {}, level: D = {}, **kwargs) -> None:
        self.fields = {**FIELDS, **fields}
        self.level = {**LEVEL, **level}

def flow(*, method: str, options: Options) -> Callable[..., dict[str, N]]:
    assert method in METHODS, 'Unknown Flow Initiation Method Specified!'
    return {
        'python': from_python(path=options.path, source=options.source, function=options.function, options=options.meta),
        'uniform': partial(uniform, levels=options.levels), 
           }[method]
