from multiprocessing.managers import BaseManager

request_collector = dict()
output_collector = dict()


class SQManager(BaseManager):
    pass


def handle():
    SQManager.register('get_request_collector', callable=lambda: request_collector)
    SQManager.register('get_output_collector', callable=lambda: output_collector)
    server_manager = SQManager(address=('', 50000), authkey=b'qwerasdf')
    server = server_manager.get_server()
    print(server.address)
    server.serve_forever()


if __name__ == '__main__':
    handle()
