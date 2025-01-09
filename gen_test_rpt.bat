coverage run --source TSDAP --parallel-mode -m pytest
coverage combine
coverage xml -i
coverage report -m
