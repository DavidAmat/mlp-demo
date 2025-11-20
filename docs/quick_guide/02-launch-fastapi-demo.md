# Launch

Follow steps in `01-launch-setup.md` to configure setup.

```bash
k apply -f fastapi-demo.yaml

# Delete
# k delete -f fastapi-demo.yaml
```

In a terminal run:
```bash
curl -X POST http://ubuntu:8080/add \
  -H "Content-Type: application/json" \
  -d '{"x": 3, "y": 4}'
```