import os
import gc
import pandas as pd
import numpy as np
from itertools import product

def downcast_dtypes(df):
    float_cols = [c for c in df if df[c].dtype == "float64"]
    int_cols = [c for c in df if df[c].dtype in ["int64", "int32"]]
    if float_cols:
        df[float_cols] = df[float_cols].astype(np.float32)
    if int_cols:
        df[int_cols] = df[int_cols].astype(np.int16)
    return df

def main():
    print("Loading raw data...")
    data_dir = 'data'
    train = pd.read_csv(os.path.join(data_dir, 'sales_train.csv'))
    test = pd.read_csv(os.path.join(data_dir, 'test.csv')).set_index('ID')
    items = pd.read_csv(os.path.join(data_dir, 'items.csv'))

    print("Cleaning anomalies...")
    train = train[train['item_price'] < 100000]
    train = train[train['item_cnt_day'] < 1000]
    train = train[train['item_price'] > 0]
    train.loc[train['item_cnt_day'] < 0, 'item_cnt_day'] = 0

    print("Building grid (shop/item pairs per month)...")
    index_cols = ['shop_id', 'item_id', 'date_block_num']
    grid = []
    for block_num in train['date_block_num'].unique():
        cur_shops = train.loc[train['date_block_num'] == block_num, 'shop_id'].unique()
        cur_items = train.loc[train['date_block_num'] == block_num, 'item_id'].unique()
        grid.append(np.array(list(product(*[cur_shops, cur_items, [block_num]])),dtype='int32'))

    grid = pd.DataFrame(np.vstack(grid), columns = index_cols, dtype=np.int32)

    print("Aggregating sales to monthly level...")
    group = train.groupby(index_cols, as_index=False).agg({'item_cnt_day': 'sum'})
    group.rename(columns={'item_cnt_day': 'item_cnt_month'}, inplace=True)

    print("Merging grid and sales...")
    matrix = pd.merge(grid, group, how='left', on=index_cols).fillna(0)
    matrix['item_cnt_month'] = matrix['item_cnt_month'].clip(0, 20).astype(np.float32)

    print("Adding test data for next month (34)...")
    test['date_block_num'] = 34
    test['item_cnt_month'] = 0
    matrix = pd.concat([matrix, test], ignore_index=True, sort=False)
    matrix.fillna(0, inplace=True)
    matrix = downcast_dtypes(matrix)
    
    print("Appending item category...")
    matrix = pd.merge(matrix, items[['item_id', 'item_category_id']], on='item_id', how='left')
    matrix['item_category_id'] = matrix['item_category_id'].astype(np.int16)

    def lag_feature(df, lags, col):
        tmp = df[['date_block_num', 'shop_id', 'item_id', col]]
        for i in lags:
            shifted = tmp.copy()
            shifted.columns = ['date_block_num', 'shop_id', 'item_id', col+'_lag_'+str(i)]
            shifted['date_block_num'] += i
            df = pd.merge(df, shifted, on=['date_block_num', 'shop_id', 'item_id'], how='left')
        return df

    print("Engineering lag features for item sales...")
    matrix = lag_feature(matrix, [1, 2, 3], 'item_cnt_month')
    
    # Adding mean encodings for item features
    print("Engineering item mean lag features...")
    group = matrix.groupby(['date_block_num', 'item_id'])['item_cnt_month'].mean().rename('item_avg_sale').reset_index()
    matrix = pd.merge(matrix, group, on=['date_block_num', 'item_id'], how='left')
    matrix = lag_feature(matrix, [1, 2, 3], 'item_avg_sale')
    matrix.drop('item_avg_sale', axis=1, inplace=True)

    # Adding mean encodings for shop features
    print("Engineering shop mean lag features...")
    group = matrix.groupby(['date_block_num', 'shop_id'])['item_cnt_month'].mean().rename('shop_avg_sale').reset_index()
    matrix = pd.merge(matrix, group, on=['date_block_num', 'shop_id'], how='left')
    matrix = lag_feature(matrix, [1, 2, 3], 'shop_avg_sale')
    matrix.drop('shop_avg_sale', axis=1, inplace=True)
    
    print("Filling missing values for lags...")
    for col in matrix.columns:
        if 'lag' in col:
            matrix[col] = matrix[col].fillna(0).astype('float32')

    # Truncate first 3 months since we use lags of up to 3 month
    matrix = matrix[matrix.date_block_num >= 3]

    print("Saving processed data...")
    matrix = downcast_dtypes(matrix)
    matrix.to_parquet(os.path.join(data_dir, 'processed_data.parquet'), index=False)
    print("Data preparation complete.")

if __name__ == "__main__":
    main()
