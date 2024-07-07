
#### `tests`
Tests to be used with `pytest`. 

###### Usage
Ensure that you are on a Linux environment with the necessary hardware (2 Nvidia GPUs with ~12GB VRAM each). To run all tests:

```bash
$ pytest
```

And, to run specific tests:

```bash
$ pytest tests/test_main.py -k 'test_homepage'
```