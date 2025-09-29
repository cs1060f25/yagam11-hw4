## API
- Endpoint: POST /county_data
- Content-Type: application/json
- Required JSON keys: {"zip": "02138", "measure_name": "Adult obesity"}
- Special case: {"coffee":"teapot"} returns HTTP 418

### curl tests
curl -s -H 'content-type: application/json' \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' \
  https://<your-project>.vercel.app/county_data

# Missing fields -> 400
curl -s -H 'content-type: application/json' -d '{}' \
  https://<your-project>.vercel.app/county_data

# Teapot -> 418
curl -s -i -H 'content-type: application/json' \
  -d '{"coffee":"teapot","zip":"02138","measure_name":"Adult obesity"}' \
  https://<your-project>.vercel.app/county_data
