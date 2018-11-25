# ethereum_parser
Infura ethereum node parser

[![Maintainability](https://api.codeclimate.com/v1/badges/7430014827a52cb6063b/maintainability)](https://codeclimate.com/github/p141592/ethereum_parser/maintainability)

* Start rabbitmq
  
    ```docker run -d -p 8080:15672 -p 5672:5672 -e RABBITMQ_DEFAULT_USER="rabbitmq" -e RABBITMQ_DEFAULT_PASS="rabbitmq" rabbitmq:3-management```

* Create rmq exchange and queues in `localhost:8080`

* Bind queues to exchange 

* Create and activate venv and install requirements

    ```python3.7 -m vnev venv && activate venv/bin/activate```

* Run ethereum_parser in environment

    ```python src/main.py```

Everything what you want you can change in env parameters
