from R5.ioc.configuration import config
from R5.ioc.injection import inject

@config(file='test_config.properties')
class Configuration:
    app_name: str
    debug: bool
    port: int
    host: str
    workers: int


@inject
def main(config: Configuration):
    print(config.app_name)
    print(config.debug)
    print(config.port, type(config.port))
    print(config.host)
    print(config.workers)

main()
