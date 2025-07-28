import pandas as pd
import numpy as np
import re
import dash_mantine_components as dmc
from dash import html

class FetchStructuredData:
    def __init__(self, file_path):
        self.file_path = file_path
        self.structure = self._load_structure_data()
        self.structure = self._clean_structure_data(self.structure)
        self.add_exit_price_column()
        self.fill_exit_price_from_status()
        self.add_filter_parameter_columns()
        self.add_stop_loss_hit_column() 
        self.add_target_hit_column()
        self.add_target_exit_diff_column()
        self.add_stoploss_exit_diff_column()
        self.add_week_str_column()
        self.add_type_column()

    def _load_structure_data(self):
        try:
            df = pd.read_csv(self.file_path)
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None

    def _clean_structure_data(self, df):
        if df is not None:
            df = df.drop(columns=['RRRValue','CallType', 'Attachment', 'ImageURL','SendTo','CallClosedBy','CallClosedDT'], errors='ignore')
        for col in ['InsertionTime', 'Validity','ModifiedDT']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                df = df[(df[col].dt.year > 2024) | ((df[col].dt.year == 2024) & (df[col].dt.month > 11))]
        for col in ['StatusDescreption', 'Header']:
            if col in df.columns:
                df = df[~df[col].astype(str).str.lower().str.contains('test', na=False)]
        if 'InsertionTime' in df.columns:
            df['Year'] = df['InsertionTime'].dt.year
            df['Month'] = df['InsertionTime'].dt.strftime('%B %Y')
        df['StatusDescreption'] = df['StatusDescreption'].str.replace(r'@\s+', '@', regex=True)
        return df

    def _extract_price(self, text):
        if pd.isna(text) or text in ["", "0"]:
            return None
        text = str(text).upper()
        # Try to extract price after '@', including ranges like '@2050-2049' (take the first number)
        match = re.search(r'@\s*(\d{1,6}(?:\.\d{1,2})?)', text)
        if match:
            price_candidate = match.group(1)
            # Avoid if price_candidate is a year (e.g., 2025, 2024, etc.)
            if not re.fullmatch(r'20\d{2}', price_candidate):
                return float(price_candidate)
        keywords = ['EXIT AT', 'BOOK PROFIT AT', 'SL HIT AT', 'EXIT', 'BOOK PROFIT']
        for keyword in keywords:
            pattern = rf'{keyword}\s*(\d{{1,6}}(?:\.\d{{1,2}})?)'
            match = re.search(pattern, text)
            if match:
                price_candidate = match.group(1)
                if not re.fullmatch(r'20\d{2}', price_candidate):
                    return float(price_candidate)
        # Avoid extracting numbers that are followed by a month name or year (to skip dates)
        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        # Find all numbers
        for m in re.finditer(r'(\d{2,6}(?:\.\d{1,2})?)', text):
            start = m.start()
            end = m.end()
            # Get the next few characters after the number
            next_part = text[end:end+6]
            prev_part = text[max(0, start-10):start]
            # Skip if the number is immediately followed by 'CE' or 'PE' (for options commodities)
            if re.match(r'(CE|PE)', text[end:end+2], re.IGNORECASE):
                continue
            # If next part starts with a month or year, skip
            if any(next_part.strip().startswith(month) for month in months):
                continue
            if re.match(r'\s*20\d{2}', next_part):  # skip if year follows
                continue
            if re.fullmatch(r'20\d{2}', m.group(1)):
                continue
            # Skip if the number is part of a price range (e.g., "at 826-828")
            if re.search(r'at\s*\d{1,6}\s*-\s*\d{1,6}', prev_part + m.group(0) + next_part, re.IGNORECASE):
                continue
            return float(m.group(1))
        return None

    def add_exit_price_column(self):
        if self.structure is None:
            return
        mask = self.structure['Status'] == "Closed"
        exit_prices = []
        for idx, row in self.structure.iterrows():
            if not mask.loc[idx]:
                exit_prices.append(np.nan)
                continue
            price = None
            for col in ['StatusDescreption', 'InternalRemark']:
                price = self._extract_price(row.get(col))
                if price not in [None, 0]:
                    break
            if price in [None, 0]:
                value = row.get('CallClosedLTP')
                if pd.notna(value) and isinstance(value, (int, float)) and float(value) != 0.0:
                    price = float(value)
            if price in [None, 0]:
                value = row.get('LastTradedPrice')
                if pd.notna(value) and isinstance(value, (int, float)) and float(value) != 0.0:
                    price = float(value)
            exit_prices.append(price if price not in [None, 0] else np.nan)
        self.structure['ExitPrice'] = exit_prices

    def fill_exit_price_from_status(self):
        if self.structure is None:
            return
        mask_nan_exit = self.structure['ExitPrice'].isna()
        for idx, row in self.structure[mask_nan_exit].iterrows():
            desc_fields = [
                str(row.get('StatusDescreption', '')).lower() if pd.notna(row.get('StatusDescreption')) else '',
                str(row.get('InternalRemark', '')).lower() if pd.notna(row.get('InternalRemark')) else ''
            ]
            found = False
            for status_desc in desc_fields:
                # Check for SL or stop loss or stoploss
                if any(word in status_desc for word in ['sl', 'stop loss', 'stoploss']):
                    stop_loss = row.get('StopLoss')
                    if pd.notna(stop_loss) and stop_loss not in [None, 0, ""]:
                        self.structure.at[idx, 'ExitPrice'] = stop_loss
                        found = True
                        break
                # Check for Target
                elif 'target' in status_desc:
                    target_price = row.get('TargetPrice')
                    if pd.notna(target_price) and target_price not in [None, 0, ""]:
                        self.structure.at[idx, 'ExitPrice'] = target_price
                        found = True
                        break
            # If nothing found, leave as NaN

    def add_filter_parameter_columns(self):
        if self.structure is None:
            return
        def calc_profit_price_change(row):
            price = row.get('Price')
            exit_price = row.get('ExitPrice')
            side = str(row.get('BuySell')).strip().upper()
            if pd.isna(price) or pd.isna(exit_price):
                return np.nan
            if side == 'SELL':
                return price - exit_price
            elif side == 'BUY':
                return exit_price - price
            else:
                return np.nan
        self.structure['ProfitPriceChange'] = self.structure.apply(calc_profit_price_change, axis=1)

    def add_stop_loss_hit_column(self):
        if self.structure is None:
            return
        def check_stop_loss_hit(desc):
            if pd.isna(desc):
                return np.nan
            desc_lower = str(desc).lower()
            if any(word in desc_lower for word in ['sl', 'stop loss', 'stoploss']):
                return 1
            return np.nan
        self.structure['StopLossHit'] = self.structure['StatusDescreption'].apply(check_stop_loss_hit)
        mask_nan = self.structure['StopLossHit'].isna()
        for idx, row in self.structure[mask_nan].iterrows():
            buy_sell = str(row.get('BuySell', '')).strip().upper()
            stop_loss = row.get('StopLoss')
            exit_price = row.get('ExitPrice')
            if pd.isna(stop_loss) or pd.isna(exit_price):
                self.structure.at[idx, 'StopLossHit'] = np.nan
                continue
            try:
                stop_loss = float(stop_loss)
                exit_price = float(exit_price)
            except Exception:
                self.structure.at[idx, 'StopLossHit'] = np.nan
                continue
            if buy_sell == 'BUY':
                self.structure.at[idx, 'StopLossHit'] = 1 if stop_loss >= exit_price else 0
            elif buy_sell == 'SELL':
                self.structure.at[idx, 'StopLossHit'] = 1 if stop_loss <= exit_price else 0
            else:
                self.structure.at[idx, 'StopLossHit'] = np.nan

    def add_target_hit_column(self):
        if self.structure is None:
            return
        def check_target_hit(desc):
            if pd.isna(desc):
                return np.nan
            # Case sensitive check for 'Target'
            if 'Target' in str(desc):
                return 1
            return np.nan
        self.structure['TargetHit'] = self.structure['StatusDescreption'].apply(check_target_hit)
        mask_nan = self.structure['TargetHit'].isna()
        for idx, row in self.structure[mask_nan].iterrows():
            buy_sell = str(row.get('BuySell', '')).strip().upper()
            target_price = row.get('TargetPrice')
            exit_price = row.get('ExitPrice')
            if pd.isna(target_price) or pd.isna(exit_price):
                self.structure.at[idx, 'TargetHit'] = np.nan
                continue
            try:
                target_price = float(target_price)
                exit_price = float(exit_price)
            except Exception:
                self.structure.at[idx, 'TargetHit'] = np.nan
                continue
            if buy_sell == 'BUY':
                self.structure.at[idx, 'TargetHit'] = 1 if exit_price >= target_price else 0
            elif buy_sell == 'SELL':
                self.structure.at[idx, 'TargetHit'] = 1 if exit_price <= target_price else 0
            else:
                self.structure.at[idx, 'TargetHit'] = np.nan

    def add_target_exit_diff_column(self):
        if self.structure is None:
            return
        def calc_target_exit_diff(row):
            target = row.get('TargetPrice')
            exit_price = row.get('ExitPrice')
            if pd.isna(target) or pd.isna(exit_price):
                return np.nan
            try:
                target = float(target)
                exit_price = float(exit_price)
                if target == 0:
                    return np.nan
                return abs((exit_price - target) / target) * 100
            except Exception:
                return np.nan
        self.structure['Target_Exit_Diff'] = self.structure.apply(calc_target_exit_diff, axis=1)

    def add_stoploss_exit_diff_column(self):
        if self.structure is None:
            return
        def calc_stoploss_exit_diff(row):
            stop_loss = row.get('StopLoss')
            exit_price = row.get('ExitPrice')
            if pd.isna(stop_loss) or pd.isna(exit_price):
                return np.nan
            try:
                stop_loss = float(stop_loss)
                exit_price = float(exit_price)
                if stop_loss == 0:
                    return np.nan
                return abs((exit_price - stop_loss) / stop_loss) * 100
            except Exception:
                return np.nan
        self.structure['StopLoss_Exit_Diff'] = self.structure.apply(calc_stoploss_exit_diff, axis=1)

    def add_week_str_column(self):
        if self.structure is None:
            return
        if 'InsertionTime' in self.structure.columns:
            def week_of_month(dt):
                if pd.isna(dt):
                    return np.nan
                first_day = dt.replace(day=1)
                dom = dt.day
                return int(np.ceil(dom / 7.0))
            week = self.structure['InsertionTime'].apply(week_of_month)
            year = self.structure['InsertionTime'].dt.year
            month = self.structure['InsertionTime'].dt.strftime('%B')
            self.structure['WeekStr'] = 'Week ' + week.astype('Int64').astype(str) + ' ' + month + ' ' + year.astype(str)
            self.structure['WeekNo'] = week.astype('Int64')
        else:
            print("InsertionTime column not found in the structure data.")
    
    def add_type_column(self):
        if self.structure is None:
            return
        def get_call_type(row):
            header = str(row.get('Header', '')).lower()
            status_desc = str(row.get('StatusDescreption', '')).lower()
            text = header + ' ' + status_desc
            if 'momentum' in text:
                return 'Momentum'
            elif 'intraday' in text:
                return 'Intraday'
            elif 'positional' in text:
                return 'Positional'
            elif 'stock of the day' in text:
                return 'Stock of the day'
            elif 'btst' in text:
                return 'BTST'
            elif 'wealth pick' in text:
                return 'Wealth pick'
            else:
                return 'Anonymous'
        self.structure['callType'] = self.structure.apply(get_call_type, axis=1)
        
    def get_structure(self):
        return self.structure
    
class backend_sender:
    def __init__(self, file_path='data/StructureCallEntries.csv'):
        self.fetcher = FetchStructuredData(file_path)
        self.df = self.fetcher.get_structure()
        self.columns = [
            "Total Calls", "Target Hit", "StopLoss Hit",
            "Neither target nor Stop loss hit - Positive",
            "Neither target nor Stop loss hit - Negative",
            "Neither target nor Stop loss hit - Redundant",
            "Total Closed Calls",
            "Open Calls - Positive", "Open Calls - Negative", "Open Calls - Redundant",
            "Total Open Calls"
        ]

    def get_data(self, start_date=None, end_date=None, exchange=None, exch_segment=None):
        df = self.df
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]
        columns = self.columns
        data = pd.DataFrame(0, index=columns, columns=["Count"])
        data.loc["Total Calls", "Count"] = df["StructuredCallEntryID"].count()
        data.loc["Target Hit", "Count"] = df[df["TargetHit"] == 1]["StructuredCallEntryID"].count()
        data.loc["StopLoss Hit", "Count"] = df[df["StopLossHit"] == 1]["StructuredCallEntryID"].count()
        data.loc["Neither target nor Stop loss hit - Positive", "Count"] = df[(df["TargetHit"] == 0) & (df["StopLossHit"] == 0) & (df["ProfitPriceChange"] > 0)]["StructuredCallEntryID"].count()
        data.loc["Neither target nor Stop loss hit - Negative", "Count"] = df[(df["TargetHit"] == 0) & (df["StopLossHit"] == 0) & (df["ProfitPriceChange"] < 0)]["StructuredCallEntryID"].count()
        data.loc["Neither target nor Stop loss hit - Redundant", "Count"] = df[(df["TargetHit"] == 0) & (df["StopLossHit"] == 0) & (df["ProfitPriceChange"] == 0)]["StructuredCallEntryID"].count()
        data.loc["Total Closed Calls", "Count"] = df[df["Status"] == "Closed"]["StructuredCallEntryID"].count()
        data.loc["Open Calls - Positive", "Count"] = df[
            (df["Status"] == "Open") &
            (
                ((df["BuySell"].str.upper() == "BUY") & (df["Price"] > df["LastTradedPrice"])) |
                ((df["BuySell"].str.upper() == "SELL") & (df["Price"] < df["LastTradedPrice"]))
            )
        ]["StructuredCallEntryID"].count()
        data.loc["Open Calls - Negative", "Count"] = df[
            (df["Status"] == "Open") &
            (
                ((df["BuySell"].str.upper() == "BUY") & (df["Price"] < df["LastTradedPrice"])) |
                ((df["BuySell"].str.upper() == "SELL") & (df["Price"] > df["LastTradedPrice"]))
            )
        ]["StructuredCallEntryID"].count()
        data.loc["Open Calls - Redundant", "Count"] = df[
            (df["Status"] == "Open") &
            (df["Price"] == df["LastTradedPrice"])
        ]["StructuredCallEntryID"].count()
        data.loc["Total Open Calls", "Count"] = df[df["Status"] == "Open"]["StructuredCallEntryID"].count()
        
        total_calls = data.loc["Total Calls", "Count"]
        if total_calls == 0:
            data["Percentage(%)"] = 0
        else:
            data["Percentage(%)"] = (data["Count"] / total_calls * 100).round(1).astype(str) + ' %'
        return data
    
    def get_data_filter_id(self, userid= None, start_date=None, end_date=None, exchange=None, exch_segment=None):
        df = self.df
        if userid is not None and len(userid) > 0:
            df = df[df['UserID'] == int(userid)]
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]
        columns = self.columns
        data = pd.DataFrame(0, index=columns, columns=["Count"])
        data.loc["Total Calls", "Count"] = df["StructuredCallEntryID"].count()
        data.loc["Target Hit", "Count"] = df[df["TargetHit"] == 1]["StructuredCallEntryID"].count()
        data.loc["StopLoss Hit", "Count"] = df[df["StopLossHit"] == 1]["StructuredCallEntryID"].count()
        data.loc["Neither target nor Stop loss hit - Positive", "Count"] = df[(df["TargetHit"] == 0) & (df["StopLossHit"] == 0) & (df["ProfitPriceChange"] > 0)]["StructuredCallEntryID"].count()
        data.loc["Neither target nor Stop loss hit - Negative", "Count"] = df[(df["TargetHit"] == 0) & (df["StopLossHit"] == 0) & (df["ProfitPriceChange"] < 0)]["StructuredCallEntryID"].count()
        data.loc["Neither target nor Stop loss hit - Redundant", "Count"] = df[(df["TargetHit"] == 0) & (df["StopLossHit"] == 0) & (df["ProfitPriceChange"] == 0)]["StructuredCallEntryID"].count()
        data.loc["Total Closed Calls", "Count"] = df[df["Status"] == "Closed"]["StructuredCallEntryID"].count()
        data.loc["Open Calls - Positive", "Count"] = df[
            (df["Status"] == "Open") &
            (
                ((df["BuySell"].str.upper() == "BUY") & (df["Price"] > df["LastTradedPrice"])) |
                ((df["BuySell"].str.upper() == "SELL") & (df["Price"] < df["LastTradedPrice"]))
            )
        ]["StructuredCallEntryID"].count()
        data.loc["Open Calls - Negative", "Count"] = df[
            (df["Status"] == "Open") &
            (
                ((df["BuySell"].str.upper() == "BUY") & (df["Price"] < df["LastTradedPrice"])) |
                ((df["BuySell"].str.upper() == "SELL") & (df["Price"] > df["LastTradedPrice"]))
            )
        ]["StructuredCallEntryID"].count()
        data.loc["Open Calls - Redundant", "Count"] = df[
            (df["Status"] == "Open") &
            (df["Price"] == df["LastTradedPrice"])
        ]["StructuredCallEntryID"].count()
        data.loc["Total Open Calls", "Count"] = df[df["Status"] == "Open"]["StructuredCallEntryID"].count()
        
        total_calls = data.loc["Total Calls", "Count"]
        if total_calls == 0:
            data["Percentage(%)"] = 0
        else:
            data["Percentage(%)"] = (data["Count"] / total_calls * 100).round(1).astype(str) + ' %'
        return data
    
    def generate_timely_summary_rows(self, start_date=None, end_date=None, exchange=None, exch_segment=None, time=None):
        df = self.df
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]

        df["InsertionTime"] = pd.to_datetime(df["InsertionTime"], errors="coerce")
        if time == "yearly":
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%Y")
        elif time == "monthly":
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%B-%Y")
        elif time == "daily": 
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%d-%b-%Y")

        rows = []

        for period, sub_df in df.groupby("MonthPeriod"):
            total_calls = len(sub_df)
            target_hit = (sub_df["TargetHit"] == 1).sum()
            stoploss_hit = (sub_df["StopLossHit"] == 1).sum()

            closed = sub_df[sub_df["ExitPrice"].notna()]
            neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
            n_pos = (
                ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
                ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))
            ).sum()

            n_neg = (
                ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
                ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))
            ).sum()

            n_red = (
                ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
                ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))
            ).sum()

            open_df = sub_df[sub_df["ExitPrice"].isna()]
            o_pos = (
                ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
                ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))
            ).sum()

            o_neg = (
                ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
                ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))
            ).sum()

            o_red = (
                ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
                ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))
            ).sum()

            total_closed = len(closed)
            total_open = len(open_df)

            count_row = html.Tr([
                html.Td(period, style={"border": "1px solid #000000", "fontWeight": "bold"}),
                html.Td(total_calls,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(target_hit,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(stoploss_hit,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(n_pos,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(n_neg,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(n_red,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(total_closed,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(o_pos,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(o_neg,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(o_red,style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(total_open,style={"border": "1px solid #000000","textAlign": "right"}),
            ])

            def pct(val):
                return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"

            percent_row = html.Tr([
                html.Td("%",style={"border": "1px solid #000000","fontWeight": "bold"}),
                html.Td("100%" if total_calls else "0%",style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(target_hit),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(stoploss_hit),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(n_pos),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(n_neg),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(n_red),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(total_closed),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(o_pos),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(o_neg),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(o_red),style={"border": "1px solid #000000","textAlign": "right"}),
                html.Td(pct(total_open),style={"border": "1px solid #000000","textAlign": "right"}),
            ])
            rows.append((period, count_row, percent_row))

        def period_key(period_str):
            try:
                if re.match(r"\d{2}-[A-Za-z]{3}-\d{4}", period_str):
                    return pd.to_datetime(period_str, format="%d-%b-%Y")
                elif "-" in period_str:
                    return pd.to_datetime(period_str, format="%B-%Y")
                else:
                    return pd.to_datetime(period_str, format="%Y")
            except Exception:
                return pd.Timestamp.min

        rows.sort(key=lambda x: period_key(x[0]), reverse=True)
        rows = [item for row in rows for item in row[1:]]
        return rows
    
    def generate_timely_summary_rows_id(self, userid = None,start_date=None, end_date=None, exchange=None, exch_segment=None, time=None):
        df = self.df
        if userid is not None and len(userid) > 0:
            df = df[df['UserID'] == int(userid)]
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]

        df["InsertionTime"] = pd.to_datetime(df["InsertionTime"], errors="coerce")
        if time == "yearly":
            df["Period"] = df["InsertionTime"].dt.strftime("%Y")
        elif time == "monthly":
            df["Period"] = df["InsertionTime"].dt.strftime("%B-%Y")
        elif time == "daily":
            df["Period"] = df["InsertionTime"].dt.strftime("%d-%b-%Y")
        else:
            df["Period"] = df["InsertionTime"].dt.strftime("%B-%Y")

        data_rows = []

        for period, sub_df in df.groupby("Period"):
            total_calls = len(sub_df)
            target_hit = (sub_df["TargetHit"] == 1).sum()
            stoploss_hit = (sub_df["StopLossHit"] == 1).sum()

            closed = sub_df[sub_df["ExitPrice"].notna()]
            neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
            n_pos = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
                    ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))).sum()
            n_neg = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
                    ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))).sum()
            n_red = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
                    ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))).sum()

            open_df = sub_df[sub_df["ExitPrice"].isna()]
            o_pos = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
                    ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))).sum()
            o_neg = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
                    ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))).sum()
            o_red = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
                    ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))).sum()

            total_closed = len(closed)
            total_open = len(open_df)

            values = [
                total_calls, target_hit, stoploss_hit,
                n_pos, n_neg, n_red,
                total_closed,
                o_pos, o_neg, o_red,
                total_open
            ]

            def pct(val):
                return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"

            percent_values = [
                "100%" if total_calls else "0%",
                pct(target_hit), pct(stoploss_hit),
                pct(n_pos), pct(n_neg), pct(n_red),
                pct(total_closed),
                pct(o_pos), pct(o_neg), pct(o_red),
                pct(total_open)
            ]

            data_rows.append((period, values, percent_values))

        def period_key(period_str):
            try:
                if re.match(r"\d{2}-[A-Za-z]{3}-\d{4}", period_str):
                    return pd.to_datetime(period_str, format="%d-%b-%Y")
                elif "-" in period_str: 
                    return pd.to_datetime(period_str, format="%B-%Y")
                else:
                    return pd.to_datetime(period_str, format="%Y")
            except Exception:
                return pd.Timestamp.min

        data_rows.sort(key=lambda x: period_key(x[0]), reverse=True)

        return data_rows

    def extract_detail_view_id(self, userid = None,start_date=None, end_date=None, exchange=None, exch_segment=None, time=None):
        df = self.df
        if userid is not None and userid > 0:
            df = df[df['UserID'] == int(userid)]
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]

        df["InsertionTime"] = pd.to_datetime(df["InsertionTime"], errors="coerce")
        if time == "yearly":
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%Y")
        else:
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%B-%Y")

        data_rows = []

        for period, sub_df in df.groupby("MonthPeriod"):
            total_calls = len(sub_df)
            target_hit = (sub_df["TargetHit"] == 1).sum()
            stoploss_hit = (sub_df["StopLossHit"] == 1).sum()

            closed = sub_df[sub_df["ExitPrice"].notna()]
            neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
            n_pos = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
                    ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))).sum()
            n_neg = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
                    ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))).sum()
            n_red = (((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
                    ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))).sum()

            open_df = sub_df[sub_df["ExitPrice"].isna()]
            o_pos = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
                    ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))).sum()
            o_neg = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
                    ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))).sum()
            o_red = (((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
                    ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))).sum()

            total_closed = len(closed)
            total_open = len(open_df)

            values = [
                total_calls, target_hit, stoploss_hit,
                n_pos, n_neg, n_red,
                total_closed,
                o_pos, o_neg, o_red,
                total_open
            ]

            def pct(val):
                return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"

            percent_values = [
                "100%" if total_calls else "0%",
                pct(target_hit), pct(stoploss_hit),
                pct(n_pos), pct(n_neg), pct(n_red),
                pct(total_closed),
                pct(o_pos), pct(o_neg), pct(o_red),
                pct(total_open)
            ]

            data_rows.append((period, values, percent_values))

        return data_rows

    def render_time_summary_data(self, time=None, exchange=None, exch_segment=None):
        df = self.df.copy()

        df["InsertionTime"] = pd.to_datetime(df["InsertionTime"], errors="coerce")
        df["Month"] = df["InsertionTime"].dt.strftime("%B %Y")
        df["Year"] = df["InsertionTime"].dt.year

        if time == "month":
            current_month = pd.to_datetime("today").strftime("%B %Y")
            df = df[df["Month"] == current_month]
        elif time == "year":
            current_year = pd.to_datetime("today").year
            df = df[df["Year"] == current_year]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]
        if time == "yearly":
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%Y")
        else:
            df["MonthPeriod"] = df["InsertionTime"].dt.strftime("%B-%Y")

        rows = []

        for period, sub_df in df.groupby("MonthPeriod"):
            total_calls = len(sub_df)
            target_hit = (sub_df["TargetHit"] == 1).sum()
            stoploss_hit = (sub_df["StopLossHit"] == 1).sum()

            closed = sub_df[sub_df["ExitPrice"].notna()]
            neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
            n_pos = (
                ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
                ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))
            ).sum()

            n_neg = (
                ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
                ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))
            ).sum()

            n_red = (
                ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
                ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))
            ).sum()

            open_df = sub_df[sub_df["ExitPrice"].isna()]
            o_pos = (
                ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
                ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))
            ).sum()

            o_neg = (
                ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
                ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))
            ).sum()

            o_red = (
                ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
                ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))
            ).sum()

            total_closed = len(closed)

            total_open = len(open_df)

            count_row = html.Tr([
                html.Td(period, style={"fontWeight": "bold"}),
                html.Td(total_calls),
                html.Td(target_hit),
                html.Td(stoploss_hit),
                html.Td(n_pos),
                html.Td(n_neg),
                html.Td(n_red),
                html.Td(total_closed),
                html.Td(o_pos),
                html.Td(o_neg),
                html.Td(o_red),
                html.Td(total_open),
            ])

            # Second row: percentages
            def pct(val):
                return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"

            percent_row = html.Tr([
                html.Td(""),
                html.Td("100%" if total_calls else "0%"),
                html.Td(pct(target_hit)),
                html.Td(pct(stoploss_hit)),
                html.Td(pct(n_pos)),
                html.Td(pct(n_neg)),
                html.Td(pct(n_red)),
                html.Td(pct(total_closed)),
                html.Td(pct(o_pos)),
                html.Td(pct(o_neg)),
                html.Td(pct(o_red)),
                html.Td(pct(total_open)),
            ])

            rows.extend([count_row, percent_row])
        return rows

    def render_type_data_gross(self, start_date=None, end_date=None, exchange=None, exch_segment=None):
        df = self.df
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]
        rows = []

        for call_type, sub_df in df.groupby("callType"):
            total_calls = len(sub_df)
            target_hit = (sub_df["TargetHit"] == 1).sum()
            stoploss_hit = (sub_df["StopLossHit"] == 1).sum()

            closed = sub_df[sub_df["ExitPrice"].notna()]
            neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
            n_pos = (
            ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
            ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))
            ).sum()

            n_neg = (
            ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
            ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))
            ).sum()

            n_red = (
            ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
            ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))
            ).sum()

            open_df = sub_df[sub_df["ExitPrice"].isna()]
            o_pos = (
            ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
            ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))
            ).sum()

            o_neg = (
            ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
            ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))
            ).sum()

            o_red = (
            ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
            ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))
            ).sum()

            total_closed = len(closed)
            total_open = len(open_df)

            count_row = html.Tr([
            html.Td(call_type, style={"fontWeight": "bold"}),
            html.Td(total_calls),
            html.Td(target_hit),
            html.Td(stoploss_hit),
            html.Td(n_pos),
            html.Td(n_neg),
            html.Td(n_red),
            html.Td(total_closed),
            html.Td(o_pos),
            html.Td(o_neg),
            html.Td(o_red),
            html.Td(total_open),
            ])

            def pct(val):
                return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"

            percent_row = html.Tr([
            html.Td(""),
            html.Td("100%" if total_calls else "0%"),
            html.Td(pct(target_hit)),
            html.Td(pct(stoploss_hit)),
            html.Td(pct(n_pos)),
            html.Td(pct(n_neg)),
            html.Td(pct(n_red)),
            html.Td(pct(total_closed)),
            html.Td(pct(o_pos)),
            html.Td(pct(o_neg)),
            html.Td(pct(o_red)),
            html.Td(pct(total_open)),
            ])

            rows.extend([count_row, percent_row])
        return rows
    
    def render_type_data_gross_id(self, userid = None, start_date=None, end_date=None, exchange=None, exch_segment=None):
        df = self.df
        if userid is not None and len(str(userid)) > 0:
            df = df[df['UserID'] == int(userid)]
        if start_date is not None:
            df = df[df['InsertionTime'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            df = df[df['InsertionTime'] <= pd.to_datetime(end_date)]
        if exchange is not None and len(exchange) > 0:
            df = df[df['Exchange'].isin(exchange)]
        if exch_segment is not None and len(exch_segment) > 0:
            df = df[df['ExchSegment'].isin(exch_segment)]
        rows = []

        for call_type, sub_df in df.groupby("callType"):
            total_calls = len(sub_df)
            target_hit = (sub_df["TargetHit"] == 1).sum()
            stoploss_hit = (sub_df["StopLossHit"] == 1).sum()

            closed = sub_df[sub_df["ExitPrice"].notna()]
            neither_df = closed[(closed["TargetHit"] != 1) & (closed["StopLossHit"] != 1)]
            n_pos = (
            ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] > neither_df["Price"])) |
            ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] < neither_df["Price"]))
            ).sum()

            n_neg = (
            ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] < neither_df["Price"])) |
            ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] > neither_df["Price"]))
            ).sum()

            n_red = (
            ((neither_df["BuySell"].str.upper() == "BUY") & (neither_df["ExitPrice"] == neither_df["Price"])) |
            ((neither_df["BuySell"].str.upper() == "SELL") & (neither_df["ExitPrice"] == neither_df["Price"]))
            ).sum()

            open_df = sub_df[sub_df["ExitPrice"].isna()]
            o_pos = (
            ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] > open_df["Price"])) |
            ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] < open_df["Price"]))
            ).sum()

            o_neg = (
            ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] < open_df["Price"])) |
            ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] > open_df["Price"]))
            ).sum()

            o_red = (
            ((open_df["BuySell"].str.upper() == "BUY") & (open_df["LastTradedPrice"] == open_df["Price"])) |
            ((open_df["BuySell"].str.upper() == "SELL") & (open_df["LastTradedPrice"] == open_df["Price"]))
            ).sum()

            total_closed = len(closed)
            total_open = len(open_df)

            count_row = html.Tr([
            html.Td(call_type, style={"fontWeight": "bold"}),
            html.Td(total_calls),
            html.Td(target_hit),
            html.Td(stoploss_hit),
            html.Td(n_pos),
            html.Td(n_neg),
            html.Td(n_red),
            html.Td(total_closed),
            html.Td(o_pos),
            html.Td(o_neg),
            html.Td(o_red),
            html.Td(total_open),
            ])

            def pct(val):
                return f"{(val / total_calls * 100):.1f}%" if total_calls else "0.0%"

            percent_row = html.Tr([
            html.Td(""),
            html.Td("100%" if total_calls else "0%"),
            html.Td(pct(target_hit)),
            html.Td(pct(stoploss_hit)),
            html.Td(pct(n_pos)),
            html.Td(pct(n_neg)),
            html.Td(pct(n_red)),
            html.Td(pct(total_closed)),
            html.Td(pct(o_pos)),
            html.Td(pct(o_neg)),
            html.Td(pct(o_red)),
            html.Td(pct(total_open)),
            ])

            rows.extend([count_row, percent_row])
        return rows        
