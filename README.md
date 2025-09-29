# County Data API (HW4)

---

### Overview

This project is an API prototype with a single endpoint, `/county_data`. It is designed to return county health ranking data from an SQLite database in JSON format. The API is deployed and accessible at the following URL:

> **Deployed on Vercel:** [https://yagam11-hw4.vercel.app/county_data](https://yagam11-hw4.vercel.app/county_data)

---

### API Details

* **Endpoint:** `POST /county_data`
* **Content-Type:** `application/json`

#### Required JSON Keys

The API requires a JSON object with two key-value pairs in the request body:

* **`zip`**: A 5-digit ZIP code as a string (e.g., `"02138"`).
* **`measure_name`**: A string representing a valid health measure.

#### Example Measures

* Violent crime rate
* Unemployment
* Children in poverty
* Diabetic screening
* Mammography screening
* Preventable hospital stays
* Uninsured
* Sexually transmitted infections
* Physical inactivity
* Adult obesity
* Premature Death
* Daily fine particulate matter

#### Special Case

* If the request body contains `"coffee": "teapot"`, the API will return an HTTP **418 I'm a Teapot** status code.

---

### Example Usage
### Valid request

```bash
curl -s -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' \
  https://yagam11-hw4.vercel.app/county_data | jq .
```

### Missing fields → 400

```bash
curl -s -H "Content-Type: application/json" \
  -d '{}' \
  https://yagam11-hw4.vercel.app/county_data
```

### Teapot → 418

```bash
curl -i -H "Content-Type: application/json" \
  -d '{"coffee":"teapot","zip":"02138","measure_name":"Adult obesity"}' \
  https://yagam11-hw4.vercel.app/county_data
```

### Nonexistent zip/measure → 404

```bash
curl -s -H "Content-Type: application/json" \
  -d '{"zip":"99999","measure_name":"Adult obesity"}' \
  https://yagam11-hw4.vercel.app/county_data
