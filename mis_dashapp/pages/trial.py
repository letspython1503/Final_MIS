import pandas as pd


def add_type_column(df):
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
        elif 'bullion' in text:
            return 'BULLION'
        elif 'wealth pick' in text:
            return 'Wealth pick'
        else:
            return 'Anonymous'
    df['callType'] = df.apply(get_call_type, axis=1)
    return df

df = pd.read_csv('data/StructureCallEntries.csv')
df = add_type_column(df)

a = df[df['Header'].str.contains('Bullion', case=False, na=False)][['InsertionTime','Header','Price', 'StopLoss','StatusDescreption','LastTradedPrice','callType']].tail(50)
a = df[['InsertionTime','Header','Price', 'StopLoss','StatusDescreption','LastTradedPrice','callType']].tail(50)
print(a)