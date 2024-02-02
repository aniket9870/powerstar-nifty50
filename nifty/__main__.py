import os
import json
from datetime import datetime

import pandas as pd

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from starlette.exceptions import HTTPException

import uvicorn

from config import path_nifty_50


def check_std_dev(filtered_nifty_df, formatted_price_data):
    '''
    Function to check if Prices are within 1 standard deviation of the prior 50 values for
    combination of symbol and price-type. (Considering all 4 price-types here - "Close", "Open", "High", "Low")
    *We can separate this function from this file and import from other file for code management*
    '''

    valid_columns = ["Close", "Open", "High", "Low"]
    std_deviation = filtered_nifty_df[valid_columns].head(50).std()
    mean = filtered_nifty_df[valid_columns].head(50).mean()
    print("mean", mean)
    print("std_dev", std_deviation)
    std_price_data = []

    for prices in formatted_price_data:
        flag = True
        for key in valid_columns:
            if abs(prices[key] - mean[key]) > std_deviation[key]:
                flag = False
                break
        if flag:
            std_price_data.append(prices)

    return std_price_data


async def http_exception(request: Request, exc: HTTPException):
    return JSONResponse({"code": 90, "message": exc.detail}, status_code=exc.status_code)


async def price_data(request: Request) -> JSONResponse:
    """
    Return price data for the requested symbol
    """
    # TODO:
    # 1) Return open, high, low & close prices for the requested symbol as json records
    # 2) Allow calling app to filter the data by year using an optional query parameter

    # Symbol data is stored in the file data/nifty50_all.csv

    symbol = request.path_params['symbol']

    if "year" in request.query_params:
        year = request.query_params['year']

        if year.isdigit():  # Checking year isdigit or not, if needed, modify to check year within expected range
            nifty_50_df = pd.read_csv(path_nifty_50, parse_dates=['Date'])

            # Filtering the data by Symbol, Year & Sorting them in descending order
            # renaming columns to lowercase, as we expect the output keys in lowercase

            filtered_nifty_df = (
                nifty_50_df.loc[(nifty_50_df['Symbol'].str.casefold() == symbol.casefold()) & (
                            nifty_50_df['Date'].dt.year == int(year)), ["Date", "Close", "Open", "High",
                                                                        "Low"]].sort_values(by='Date',
                                                                                            ascending=False).rename(
                    columns=str.lower)
            )
            filtered_nifty_df['date'] = filtered_nifty_df['date'].dt.strftime('%d/%m/%Y')

            if filtered_nifty_df.empty:
                raise HTTPException(status_code=400,
                                    detail=json.dumps({"code": 22, "message": "No detail found for specified year"}))
        else:
            raise HTTPException(status_code=400,
                                detail=json.dumps({"code": 12, "message": "Invalid year format received"}))

    else:
        nifty_50_df = pd.read_csv(path_nifty_50, parse_dates=['Date'])

        # Filtering the data by Symbol & Sorting them in descending order
        # renaming columns to lowercase, as we expect the output keys in lowercase

        filtered_nifty_df = (
            nifty_50_df.loc[
                nifty_50_df['Symbol'].str.casefold() == symbol.casefold(), ["Date", "Close", "Open", "High", "Low"]]
                .sort_values(by='Date', ascending=False).rename(columns=str.lower)
        )
        filtered_nifty_df['date'] = filtered_nifty_df['date'].dt.strftime('%d/%m/%Y')

        if filtered_nifty_df.empty:
            raise HTTPException(status_code=400,
                                detail=json.dumps({"code": 22, "message": "No detail found for specified symbol"}))

    return JSONResponse(json.loads(filtered_nifty_df.to_json(orient="records")))


async def add_price_data(request: Request) -> JSONResponse:
    symbol = request.path_params['symbol']
    price_json = await request.json()

    '''Validation of the data received and make data compatible to enter in to CSV.'''

    valid_keys = ("date", "open", "close", "high", "low")
    date_format = "%d/%m/%Y"
    formatted_price_data = []

    for each_price in price_json:
        item = {"Symbol": symbol.upper()}
        for key, value in each_price.items():
            key = key.casefold()
            if key not in valid_keys:
                raise HTTPException(status_code=400,
                                    detail=json.dumps({"code": 30, "message": "Invalid price type"}))
            elif key == "date":
                try:
                    # converting and replacing date format to match it in csv file ("%Y-%m-%d")
                    item["Date"] = datetime.strptime(value, date_format).strftime("%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400,
                                        detail=json.dumps({"code": 30, "message": "Invalid date format"}))
            else:
                item[key.capitalize()] = value
        formatted_price_data.append(item)

    nifty_df = pd.read_csv(path_nifty_50)                   # Reading nifty50_all.csv
    nifty_df.columns = nifty_df.columns.str.capitalize()

    # Filtering the data by symbol and sorting it descending by Date

    filtered_nifty_df = (
        nifty_df.loc[nifty_df['Symbol'].str.casefold() == symbol.casefold(), ["Date", "Close", "Open", "High", "Low"]]
            .sort_values(by='Date', ascending=False)
    )

    std_price_data = check_std_dev(filtered_nifty_df, formatted_price_data)

    # Checking duplicate entries before appending the final data to CSV,
    # although checking NOT just by ONLY Date but all columns
    print(std_price_data)
    if std_price_data:
        std_price_data_df = pd.DataFrame.from_records(std_price_data)
        std_price_data_merge_df = pd.merge(std_price_data_df, nifty_df,
                                           on=["Date", "Symbol", "Close", "Open", "High", "Low"], how='inner')
        std_price_data_df = pd.concat([std_price_data_df, std_price_data_merge_df], ignore_index=True)
        std_price_data_df['Duplicated'] = std_price_data_df.duplicated(keep=False)
        std_price_data_final_df = std_price_data_df[~std_price_data_df['Duplicated']]
        del std_price_data_final_df['Duplicated']

        # updating the final data in CSV file
        updated_df = pd.concat([nifty_df, std_price_data_final_df], ignore_index=True)
        updated_df.to_csv(path_nifty_50, index=False)

    return JSONResponse({"code": 10, 'message': 'Details updated in CSV'})

# Exception Handlers
exception_handlers = {
    HTTPException: http_exception
}

# URL routes
app = Starlette(debug=True, routes=[
    Route('/nifty/stocks/{symbol}', price_data),
    Route('/nifty/stocks/{symbol}/add', add_price_data, methods=['POST'])
], exception_handlers=exception_handlers)


def main() -> None:
    """
    start the server
    """
    uvicorn.run(app, host='0.0.0.0', port=8888)


# Entry point
main()
