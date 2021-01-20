

```sh
kill -9  $(ps -ef | grep 'kafka' | grep 'java' | awk '{print $2}')
kill -9  $(ps -ef | grep 'kafka' | grep 'python' | awk '{print $2}')
```

