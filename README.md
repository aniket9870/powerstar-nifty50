# Powerstar development test project

This project is a partially implemented web API that returns historical stock market data (open, close, high and low prices) for stocks in the [Indian Nifty50](https://www.nseindia.com/) stock index.

The project is implemented using python 3.9 and the [starlette](https://www.starlette.io/) ASGI web framework.

## Getting started
* Clone or fork this repository
* Install requirements using `pip install -r requirements.txt`
* Run the server using `python -m nifty`
* Access the endpoint at `localhost:8888/nifty/stocks/{symbol}`


## Summary of completed requirements

### 1) Get list of historical price data

`GET /nifty/stocks/tatamotors/`

### Response

```json
[
    {
        "date": "26/12/2003",
        "open": 435.8,
        "high": 440.5,
        "low": 431.65,
        "close": 438.6
    },
    {
        ...
    }
]
```

### 2) filter price data by year

`GET /nifty/stocks/tatamotors/?year=2017`

```json
[
    {
        "date": "29/12/2017",
        "open": 390.8,
        "high": 410.5,
        "low": 385.65,
        "close": 405.6
    },
    {
        ...
    }
]
```

### 3) Adding new data

### Request

`POST /nifty/stocks/tatamotors/add`

```json
[
    {
      "date":"01/02/2024",
      "close":310.9,
      "open":303.2,
      "high":311.3,
      "low":302.55
    },
    {
      "date":"03/01/2024",
      "close":304.1,
      "open":303.44,
      "high":306.3,
      "low":301.25
    }
]
```


### Response

```json
{
    "code": 10,
    "message": "Details updated in CSV"
}
```

## Additional information
* Compatible with python 3.9 or above
* If you have questions please email aniket9870@gmail.com

Thanks for this wonderful experience!
